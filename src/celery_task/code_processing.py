from datetime import datetime
import requests
import torch

from celery import Celery
from celery.result import AsyncResult
from sqlmodel import create_engine, Session

from src.config import settings
from src.persistence import ReportFile, Report
from src.constants import LANGUAGES
import os
from .util import codeql, get_vulnerability_model_tokenizer

vulnerability_tokenizer, vulnerability_model = get_vulnerability_model_tokenizer(settings.DEVICE, settings.VULNERABILITY_MODEL_NAME, settings.VULNERABILITY_MODEL_PATH)
db_engine = create_engine(str(settings.DATABASE_URL))

tensor_cwe_mapping = ["cwe-79", "cwe-125", "cwe-20", "cwe-787"]

celery_app = Celery(
    "celery",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
    broker_connection_retry_on_startup=True
)


@celery_app.task()
def celery_machine_code_detection_task(data):
    if not data["report_id"] or not data["path"] or not data["filename_list"] or not data["programming_language"]:
        print("validate failed")
        return

    programming_language = data["programming_language"]
    filename_list: list[str] = data["filename_list"]
    path = data["path"]
    report_id = int(data["report_id"])

    supported_extension = None
    supported_language_name = None
    for supported_language in LANGUAGES:
        if programming_language == supported_language["value"]:
            supported_extension = supported_language["extension"]
            supported_language_name = supported_language["name"]
            break

    if supported_extension is None:
        print("Language is not supported")
        return

    report_files = []
    sent_task = []

    for filename in filename_list:
        extension = filename[filename.rindex("."):]
        if not extension or extension != supported_extension:
            # report_files.append(ReportFile(
            #         report_id=report_id,
            #         filename=filename,
            #         programming_language="undefined",
            #         machine_code_probability=0,
            #         created_at=datetime.now(),
            #         updated_at=datetime.now()))
            continue

        task_data = {
            "path": path,
            "filename": filename,
            "programming_language": supported_language_name
        }
        task = celery_app.send_task(
            'src.celery_task.machine_detection_inference.inference',
            args=[task_data],
            queue="inference"
        )
        sent_task.append({
            "task": task,
            "filename": filename,
            "programming_language": supported_language_name
        })

    while len(sent_task) > 0:
        remaining_task = []
        for task in sent_task:
            task_result = AsyncResult(task["task"].id)
            if task_result.status == "SUCCESS":
                report_files.append(ReportFile(
                    report_id=report_id,
                    filename=task["filename"],
                    programming_language=task["programming_language"],
                    machine_code_probability=task_result.result,
                    created_at=datetime.now(),
                    updated_at=datetime.now()))
            elif task_result.status == "FAILURE":
                report_files.append(ReportFile(
                    report_id=report_id,
                    filename=task["filename"],
                    programming_language=task["programming_language"],
                    machine_code_probability=-1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()))
            else:
                remaining_task.append(task)

        sent_task = remaining_task

    try:
        with Session(db_engine) as db_session:
            with db_session.begin():
                for report_file in report_files:
                    db_session.add(report_file)

                report = db_session.get(Report, report_id)
                if not report:
                    raise Exception("Report not found")

                report.machine_code_detect_status = 1
                db_session.add(report)

    except Exception as e:
        print(e)

    # try:
    #     shutil.rmtree(path)
    # except IOError:
    #     return


@celery_app.task()
def celery_codeql_task(data):
    if not data or not isinstance(data, dict) or "path" not in data or "report_id" not in data or "programming_language" not in data or "filename_list" not in data:
        print("Sent data is invalid: ", data)
        return

    path_to_source = data["path"]
    report_id = data["report_id"]
    filename_list: list[str] = data["filename_list"]
    programming_language = data["programming_language"]
    results_folder = ""
    success = True

    cwe_list = check_cwe(path_to_source, filename_list)

    if len(cwe_list) == 0:
        results_folder = codeql.create_results_folder(path_to_source)
        print("Results folder created at:", results_folder)
        codeql.create_empty_result(results_folder)

        send_codeql_result(False, report_id, results_folder)
        return

    try:
        if not os.path.exists(path_to_source) or not os.path.isdir(path_to_source):
            print("Invalid folder path: " + path_to_source)
            return

        database_folder = codeql.create_database_folder(path_to_source)
        print("Database folder created at:", database_folder)

        database_path = codeql.create_database("database", database_folder, path_to_source, programming_language)
        if database_path:
            print(f"Database created at: {database_path}")
        else:
            print(f"Failed to create database")

        results_folder = codeql.create_results_folder(path_to_source)
        print("Results folder created at:", results_folder)

        for file in os.listdir(database_folder):
            if file.endswith(".ql"):
                print("Analyzing database:", file)
                codeql.analyze_database(database_folder, results_folder, file, programming_language, cwe_list)
                print("Analysis completed.")

        codeql.merge_results(results_folder)
        print("Results merged into a single file: codeql.csv")
    except Exception as e:
        print(e)
        success = False

    send_codeql_result(success, report_id, results_folder)


def check_cwe(path_to_source, filename_list):
    cwe_list = []
    for filename in filename_list:
        fullpath = os.path.join(path_to_source, filename)
        with open(fullpath, "r") as f:
            content = f.read()

        if not content:
            print("No content")
            continue

        with torch.no_grad():
            tokenized_code = vulnerability_tokenizer(
                content,
                return_tensors="pt",
                padding='max_length',
                max_length=512,
                truncation=True
            ).to(settings.DEVICE)

            result = vulnerability_model(tokenized_code)
            for i in range(4):
                scalar_result = result[0][i].item()
                if scalar_result > 0.5 and tensor_cwe_mapping[i] not in cwe_list:
                    cwe_list.append(tensor_cwe_mapping[i])

    return cwe_list


def send_codeql_result(process_status, report_id, results_folder):
    login_response = requests.post(
        settings.RAILS_API_LOGIN_URL,
        {
            "email": settings.RAILS_API_EMAIL,
            "password": settings.RAILS_API_PASSWORD
        }
    )

    if login_response.status_code != 202:
        print("Cannot login to Rails")
        return

    login_response_json = login_response.json()
    token = login_response_json['token']
    collect_codeql_response = requests.post(
        settings.COLLECT_CODEQL_RESULT_URL.replace(":report_id", report_id),
        {
            "status": process_status,
            "result_dir": results_folder
        },
        headers={
            'Authorization': f'Bearer {token}'
        }
    )

    if collect_codeql_response.status_code != 200:
        print("Cannot push codeql result files to Rails. Response: ", collect_codeql_response.status_code, collect_codeql_response.text)
        return

    print("Success")

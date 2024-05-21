from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.config import app_configs, settings
from src.api.dto import DatasetProcessInfo
# from src.celery_task import celery_machine_code_detection_task, celery_codeql_task
import celery
app = FastAPI(**app_configs)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGINS_REGEX,
    allow_credentials=True,
    allow_methods=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
    allow_headers=settings.CORS_HEADERS,
)

celery_app = celery.Celery(
    "celery",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
    broker_connection_retry_on_startup=True
)


@app.get("/healthcheck")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/dataset/process")
async def process_dataset(dataset_info: DatasetProcessInfo):
    print("File path: ", dataset_info.folder_path)
    print("Dataset ID: ", dataset_info.dataset_id)
    print("File list: ", dataset_info.file_list)
    print("Programming language: ", dataset_info.programming_language)

    celery_machine_code_detection_data = {
        "report_id": dataset_info.report_id,
        "path": dataset_info.folder_path,
        "filename_list": dataset_info.file_list,
        "programming_language": dataset_info.programming_language
    }

    machine_code_detection_task = celery_app.send_task(
        "src.celery_task.code_processing.celery_machine_code_detection_task",
        args=[celery_machine_code_detection_data]
    )
    # machine_code_detection_task = celery_machine_code_detection_task.delay(celery_machine_code_detection_data)

    celery_codeql_data = {
        "path": dataset_info.folder_path,
        "report_id": dataset_info.report_id,
        "filename_list": dataset_info.file_list,
        "programming_language": dataset_info.programming_language
    }
    codeql_task = celery_app.send_task(
        "src.celery_task.code_processing.celery_codeql_task",
        args=[celery_codeql_data]
    )
    # codeql_task = celery_codeql_task.delay(celery_codeql_data)

    return {
        "message": "ok",
        "machine_code_detect_task": machine_code_detection_task.id,
        "codeql_task": codeql_task.id
    }

import os.path

import torch
from celery import Celery
from sqlmodel import create_engine

from src.celery_task.util import ModelInfo, ModelManager
from src.config import settings

# model_info_list = [
#     ModelInfo(settings.MODEL_NAME, settings.MODEL_PATH, ["Python3"], "cuda")
# ]
model_info_list = [
    ModelInfo(model_name, model_path, [language], settings.DEVICE)
    for language, model_name, model_path in zip(settings.LANGUAGES, settings.MODEL_NAMES, settings.MODEL_PATHS)
]

model_manager = ModelManager(model_info_list)
model_manager.load()

db_engine = create_engine(str(settings.DATABASE_URL))

celery_app = Celery(
    "celery",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
    broker_connection_retry_on_startup=True
)


@celery_app.task()
def inference(data):
    path = data["path"]
    filename = data["filename"]
    programming_language = data["programming_language"]

    model_info = model_manager.get_model_by_language(programming_language)
    if model_info is None:
        print("No model info found")
        return -1

    try:
        fullpath = os.path.join(path, filename)
        with open(fullpath, "r") as f:
            content = f.read()

        if not content:
            print("No content")
            return 0

        with torch.no_grad():
            tokenized_code = model_info.tokenizer(
                content,
                return_tensors="pt",
                padding='max_length',
                max_length=512,
                truncation=True
            ).to(model_info.device)

            result = model_info.model(tokenized_code)

        return result.item()

    except IOError:
        print(f"Can't open {path}/{filename}")

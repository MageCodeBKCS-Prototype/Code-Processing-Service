from sqlmodel import SQLModel
from typing import Optional


class DatasetCreate(SQLModel):
    name: str
    programming_language: str


class DatasetProcessInfo(SQLModel):
    report_id: str
    folder_path: str
    dataset_id: str
    file_list: list[str]
    programming_language: str

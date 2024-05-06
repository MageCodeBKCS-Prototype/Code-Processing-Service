from sqlmodel import SQLModel, Field, Column, BigInteger
from typing import Optional
from datetime import datetime


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    dataset_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    status: Optional[int]
    error: Optional[str]
    stdout: Optional[str]
    stderr: Optional[str]
    exit_status: Optional[int]
    memory: Optional[int]
    run_time: Optional[float]
    created_at: datetime = Field(default=None)
    updated_at: datetime = Field(default=None)
    machine_code_detect_status: int = Field(default=0)

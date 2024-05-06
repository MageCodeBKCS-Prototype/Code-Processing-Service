import datetime

from sqlmodel import SQLModel, Field, Column, BigInteger


class ReportFile(SQLModel, table=True):
    __tablename__ = "report_files"

    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    report_id: int = Field(sa_column=Column(BigInteger))
    filename: str = Field(nullable=False)
    programming_language: str = Field(nullable=False)
    machine_code_probability: float = Field(nullable=False)
    created_at: datetime.datetime
    updated_at: datetime.datetime

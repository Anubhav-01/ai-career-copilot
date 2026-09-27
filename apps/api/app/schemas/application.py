import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.application import APPLICATION_STATUSES


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=255)
    job_title: str = Field(min_length=1, max_length=255)
    job_url: str | None = Field(default=None, max_length=1000)
    location: str | None = Field(default=None, max_length=255)
    salary: str | None = Field(default=None, max_length=100)
    status: str = Field(default="saved")
    applied_at: datetime | None = None
    interview_date: datetime | None = None
    notes: str | None = Field(default=None, max_length=10000)
    job_id: uuid.UUID | None = None
    resume_id: uuid.UUID | None = None

    def validate_status(self) -> None:
        if self.status not in APPLICATION_STATUSES:
            raise ValueError(f"status must be one of {APPLICATION_STATUSES}")


class ApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, max_length=255)
    job_title: str | None = Field(default=None, max_length=255)
    job_url: str | None = Field(default=None, max_length=1000)
    location: str | None = Field(default=None, max_length=255)
    salary: str | None = Field(default=None, max_length=100)
    status: str | None = None
    applied_at: datetime | None = None
    interview_date: datetime | None = None
    notes: str | None = Field(default=None, max_length=10000)
    resume_id: uuid.UUID | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company: str
    job_title: str
    job_url: str | None = None
    location: str | None = None
    salary: str | None = None
    status: str
    applied_at: datetime | None = None
    interview_date: datetime | None = None
    notes: str | None = None
    job_id: uuid.UUID | None = None
    resume_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

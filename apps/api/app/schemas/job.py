import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobAnalyzeRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    source_url: str | None = Field(default=None, max_length=1000)
    description: str = Field(min_length=100, max_length=50000)


class JobAnalysis(BaseModel):
    """Validated structure for LLM/rule-based job description analysis."""

    job_title: str = ""
    company: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience_years_min: int | None = None
    responsibilities: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    seniority: str | None = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str | None = None
    location: str | None = None
    source_url: str | None = None
    created_at: datetime


class JobDetail(JobOut):
    description_text: str
    analysis: JobAnalysis | None = None

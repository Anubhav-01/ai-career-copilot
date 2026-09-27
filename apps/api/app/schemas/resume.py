"""Resume schemas.

`ResumeExtraction` is the guarded contract for LLM extraction output:
anything the model returns is validated against it before persistence.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExperienceItem(BaseModel):
    title: str = ""
    company: str = ""
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    bullets: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    degree: str = ""
    institution: str = ""
    field: str | None = None
    start_year: str | None = None
    end_year: str | None = None


class ProjectItem(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    url: str | None = None


class ResumeExtraction(BaseModel):
    """Structured resume content. Every field must be grounded in the
    resume text - the extraction pipeline cross-checks values against the
    raw text and drops anything unsupported (anti-hallucination)."""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class ResumeSkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    normalized: str
    category: str | None = None
    evidence: str | None = None
    source: str


class ResumeSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_type: str
    title: str | None = None
    content: str
    order_index: int


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    original_filename: str
    file_type: str
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ResumeDetail(ResumeOut):
    parsed: ResumeExtraction | None = None
    skills: list[ResumeSkillOut] = Field(default_factory=list)
    sections: list[ResumeSectionOut] = Field(default_factory=list)


class BulletImprovementRequest(BaseModel):
    bullet: str = Field(min_length=5, max_length=1000)
    target_role: str | None = Field(default=None, max_length=255)


class BulletImprovement(BaseModel):
    original: str
    improved: str
    rationale: str
    missing_metric_suggestion: str | None = None


class TailoringSuggestion(BaseModel):
    """Job-specific resume tailoring output (no fabricated experience)."""

    skills_to_emphasize: list[str] = Field(default_factory=list)
    keywords_to_include: list[str] = Field(default_factory=list)
    sections_to_modify: list[str] = Field(default_factory=list)
    bullets_to_improve: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    summary: str = ""

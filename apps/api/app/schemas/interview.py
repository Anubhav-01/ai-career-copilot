import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

QUESTION_CATEGORIES = (
    "technical",
    "behavioral",
    "situational",
    "project",
    "resume",
    "system_design",
    "hr",
)


class InterviewCreateRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=255)
    resume_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    mode: str = Field(default="mock", pattern="^(prep|mock)$")
    question_count: int = Field(default=6, ge=3, le=15)
    categories: list[str] | None = None


class GeneratedQuestion(BaseModel):
    """Validated structure for LLM question generation."""

    question: str
    category: str = "technical"
    difficulty: str = "medium"
    grounding: str = ""  # what resume/job evidence prompted this question


class GeneratedQuestionList(BaseModel):
    questions: list[GeneratedQuestion] = Field(default_factory=list)


class InterviewQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_index: int
    category: str
    difficulty: str
    question: str
    grounding: str | None = None
    answered: bool = False


class AnswerRequest(BaseModel):
    question_id: uuid.UUID
    answer: str = Field(min_length=1, max_length=10000)


class InterviewFeedback(BaseModel):
    """Validated structure for LLM answer evaluation.

    All dimensions are text-based judgments only; the system makes no
    psychological or personality claims."""

    score: float = Field(ge=0, le=100)
    relevance: float = Field(ge=0, le=100)
    technical_correctness: float = Field(ge=0, le=100)
    clarity: float = Field(ge=0, le=100)
    completeness: float = Field(ge=0, le=100)
    structure: float = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggested_structure: str = ""
    improvement_tips: list[str] = Field(default_factory=list)


class AnswerResult(BaseModel):
    question_id: uuid.UUID
    feedback: InterviewFeedback
    next_question: InterviewQuestionOut | None = None
    interview_completed: bool = False


class InterviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_role: str
    difficulty: str
    mode: str
    status: str
    resume_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    created_at: datetime
    completed_at: datetime | None = None


class InterviewDetail(InterviewOut):
    questions: list[InterviewQuestionOut] = Field(default_factory=list)


class InterviewReport(BaseModel):
    overall_score: float = 0
    answered: int = 0
    total_questions: int = 0
    category_scores: dict[str, float] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    improvement_tips: list[str] = Field(default_factory=list)

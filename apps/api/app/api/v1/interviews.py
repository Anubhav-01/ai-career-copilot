import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.interview import (
    AnswerRequest,
    AnswerResult,
    InterviewCreateRequest,
    InterviewDetail,
    InterviewOut,
    InterviewQuestionOut,
    InterviewReport,
)
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("", response_model=InterviewDetail, status_code=201)
def create_interview(
    payload: InterviewCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewDetail:
    interview = InterviewService(db).create(user, payload)
    return InterviewDetail.model_validate(interview)


@router.get("", response_model=list[InterviewOut])
def list_interviews(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[InterviewOut]:
    return [
        InterviewOut.model_validate(i)
        for i in InterviewService(db).interviews.list_for_user(user.id)
    ]


@router.get("/{interview_id}", response_model=InterviewDetail)
def get_interview(
    interview_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewDetail:
    interview = InterviewService(db).get_owned(user, interview_id)
    return InterviewDetail.model_validate(interview)


@router.post("/{interview_id}/answer", response_model=AnswerResult)
def answer_question(
    interview_id: uuid.UUID,
    payload: AnswerRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnswerResult:
    feedback, next_question, completed = InterviewService(db).answer(
        user, interview_id, payload.question_id, payload.answer
    )
    return AnswerResult(
        question_id=payload.question_id,
        feedback=feedback,
        next_question=(
            InterviewQuestionOut.model_validate(next_question)
            if next_question else None
        ),
        interview_completed=completed,
    )


@router.get("/{interview_id}/report", response_model=InterviewReport)
def interview_report(
    interview_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewReport:
    return InterviewService(db).report(user, interview_id)

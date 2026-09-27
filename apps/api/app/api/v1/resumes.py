import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db, get_session_factory
from app.models.user import User
from app.schemas.analysis import ResumeAnalysisOut
from app.schemas.common import MessageResponse
from app.schemas.resume import (
    BulletImprovement,
    BulletImprovementRequest,
    ResumeDetail,
    ResumeOut,
    TailoringSuggestion,
)
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resumes", tags=["resumes"])


def _process_in_background(resume_id: uuid.UUID) -> None:
    """Background task entrypoint with its own DB session."""
    session = get_session_factory()()
    try:
        ResumeService(session).process(resume_id)
    finally:
        session.close()


@router.post("/upload", response_model=ResumeOut, status_code=202)
async def upload_resume(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeOut:
    content = await file.read()
    resume = ResumeService(db).upload(user, file.filename or "resume.pdf", content, title)
    db.commit()  # persist before the background task picks it up
    background.add_task(_process_in_background, resume.id)
    return ResumeOut.model_validate(resume)


@router.get("", response_model=list[ResumeOut])
def list_resumes(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ResumeOut]:
    return [
        ResumeOut.model_validate(r)
        for r in ResumeService(db).resumes.list_for_user(user.id)
    ]


@router.get("/{resume_id}", response_model=ResumeDetail)
def get_resume(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeDetail:
    resume = ResumeService(db).get_owned(user, resume_id)
    return ResumeDetail.model_validate(resume)


@router.delete("/{resume_id}", response_model=MessageResponse)
def delete_resume(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    ResumeService(db).delete(user, resume_id)
    return MessageResponse(message="Resume deleted.")


@router.post("/{resume_id}/analyze", response_model=ResumeAnalysisOut)
def analyze_resume(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeAnalysisOut:
    return ResumeAnalysisOut.model_validate(ResumeService(db).analyze(user, resume_id))


@router.get("/{resume_id}/analysis", response_model=ResumeAnalysisOut | None)
def latest_analysis(
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeAnalysisOut | None:
    service = ResumeService(db)
    service.get_owned(user, resume_id)  # ownership check
    analysis = service.resumes.latest_analysis(resume_id)
    return ResumeAnalysisOut.model_validate(analysis) if analysis else None


@router.post("/{resume_id}/improve-bullet", response_model=BulletImprovement)
def improve_bullet(
    resume_id: uuid.UUID,
    payload: BulletImprovementRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BulletImprovement:
    return ResumeService(db).improve_bullet(
        user, resume_id, payload.bullet, payload.target_role
    )


@router.post("/{resume_id}/tailor/{job_id}", response_model=TailoringSuggestion)
def tailor_resume(
    resume_id: uuid.UUID,
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TailoringSuggestion:
    return ResumeService(db).tailor(user, resume_id, job_id)

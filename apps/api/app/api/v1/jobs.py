import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.job import JobAnalyzeRequest, JobDetail, JobOut
from app.schemas.match import MatchOut, MatchRequest
from app.services.job_service import JobService
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/analyze", response_model=JobDetail, status_code=201)
def analyze_job(
    payload: JobAnalyzeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDetail:
    return JobDetail.model_validate(JobService(db).analyze_and_store(user, payload))


@router.get("", response_model=list[JobOut])
def list_jobs(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[JobOut]:
    return [JobOut.model_validate(j) for j in JobService(db).jobs.list_for_user(user.id)]


@router.get("/{job_id}", response_model=JobDetail)
def get_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobDetail:
    return JobDetail.model_validate(JobService(db).get_owned(user, job_id))


@router.delete("/{job_id}", response_model=MessageResponse)
def delete_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    JobService(db).delete(user, job_id)
    return MessageResponse(message="Job deleted.")


@router.post("/{job_id}/match", response_model=MatchOut)
def match_job(
    job_id: uuid.UUID,
    payload: MatchRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchOut:
    return MatchOut.model_validate(
        MatchingService(db).match(user, job_id, payload.resume_id)
    )


@router.get("/{job_id}/match/{resume_id}", response_model=MatchOut | None)
def latest_match(
    job_id: uuid.UUID,
    resume_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchOut | None:
    match = MatchingService(db).matches.latest_for_pair(user.id, resume_id, job_id)
    return MatchOut.model_validate(match) if match else None

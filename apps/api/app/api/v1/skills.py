import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.resume import ResumeRepository
from app.schemas.match import LearningRoadmapOut, SkillGapItem
from app.schemas.resume import ResumeSkillOut
from app.services.roadmap_service import RoadmapService
from app.services.skill_gap_service import SkillGapService

router = APIRouter(tags=["skills"])


@router.get("/skills", response_model=list[ResumeSkillOut])
def list_skills(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ResumeSkillOut]:
    skills = ResumeRepository(db).skills_for_user(user.id)
    unique: dict[str, ResumeSkillOut] = {}
    for skill in skills:
        unique.setdefault(skill.normalized, ResumeSkillOut.model_validate(skill))
    return list(unique.values())


@router.post(
    "/skills/gaps/{resume_id}/{job_id}", response_model=list[SkillGapItem]
)
def analyze_gaps(
    resume_id: uuid.UUID,
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SkillGapItem]:
    gaps = SkillGapService(db).analyze(user, resume_id, job_id)
    return [SkillGapItem.model_validate(g) for g in gaps]


@router.get("/skills/gaps", response_model=list[SkillGapItem])
def list_gaps(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[SkillGapItem]:
    return [
        SkillGapItem.model_validate(g) for g in SkillGapService(db).list_gaps(user)
    ]


@router.post("/learning/roadmaps/{gap_id}", response_model=LearningRoadmapOut, status_code=201)
def generate_roadmap(
    gap_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LearningRoadmapOut:
    return LearningRoadmapOut.model_validate(RoadmapService(db).generate(user, gap_id))


@router.get("/learning/roadmaps", response_model=list[LearningRoadmapOut])
def list_roadmaps(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[LearningRoadmapOut]:
    return [
        LearningRoadmapOut.model_validate(r)
        for r in RoadmapService(db).list_for_user(user)
    ]

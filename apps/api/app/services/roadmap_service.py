"""Personalized learning roadmaps for skill gaps (LLM-generated, schema-
validated; course URLs are deliberately never produced)."""
import uuid

from sqlalchemy.orm import Session

from app.ai.guardrails import call_structured
from app.ai.llm.factory import get_llm_provider
from app.ai.parsing.skills import skill_category
from app.ai.prompts import SYSTEMS, build_prompt
from app.core.errors import NotFoundError
from app.models.match import LearningRoadmap
from app.models.user import User
from app.repositories.match import MatchRepository
from app.repositories.resume import ResumeRepository
from app.schemas.match import LearningRoadmapSchema


class RoadmapService:
    def __init__(self, db: Session):
        self.db = db
        self.matches = MatchRepository(db)
        self.resumes = ResumeRepository(db)

    def generate(self, user: User, gap_id: uuid.UUID) -> LearningRoadmap:
        gap = next(
            (g for g in self.matches.gaps_for_user(user.id) if g.id == gap_id), None
        )
        if gap is None:
            raise NotFoundError("Skill gap not found.")

        # Ground the roadmap in what the user already knows.
        user_skills = sorted({
            s.normalized for s in self.resumes.skills_for_user(user.id)
        })
        target_category = skill_category(gap.normalized)
        related = [
            s for s in user_skills
            if target_category and skill_category(s) == target_category
        ]

        prompt = build_prompt(
            instruction=(
                "Create a practical week-by-week learning roadmap for the"
                " target skill, tailored to what the learner already knows."
                " Each stage needs a focus and one concrete practice task."
                " Do NOT include course names, URLs or paid products."
            ),
            context={
                "skill": gap.skill,
                "priority": gap.priority,
                "known_related_skills": related[:6],
                "all_known_skills": user_skills[:20],
            },
            schema_hint=("{skill, priority, prerequisites[],"
                         " stages[{period, focus, practice_task}],"
                         " project_idea, estimated_weeks}"),
        )
        roadmap_schema = call_structured(
            get_llm_provider(), "learning_roadmap", SYSTEMS["learning_roadmap"],
            prompt, LearningRoadmapSchema, max_tokens=1200,
        )
        roadmap_schema.skill = gap.skill
        roadmap_schema.priority = gap.priority

        return self.matches.add_roadmap(LearningRoadmap(
            user_id=user.id,
            skill=gap.skill,
            priority=gap.priority,
            estimated_weeks=roadmap_schema.estimated_weeks,
            content=roadmap_schema.model_dump(),
        ))

    def list_for_user(self, user: User) -> list[LearningRoadmap]:
        return self.matches.roadmaps_for_user(user.id)

"""Dashboard aggregates (cached per user; invalidated on writes)."""
from collections import Counter

from sqlalchemy.orm import Session

from app.core.cache import get_cache
from app.core.config import get_settings
from app.models.user import User
from app.repositories.application import ApplicationRepository
from app.repositories.interview import InterviewRepository
from app.repositories.job import JobRepository
from app.repositories.match import MatchRepository
from app.repositories.resume import ResumeRepository
from app.repositories.user import UserRepository
from app.schemas.dashboard import (
    AdminStats,
    DashboardOut,
    FunnelStage,
    InterviewPerformancePoint,
    MatchDistributionBucket,
    ScorePoint,
    SkillCoverageItem,
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user: User) -> DashboardOut:
        cache = get_cache()
        cache_key = f"dashboard:{user.id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return DashboardOut.model_validate(cached)

        resumes = ResumeRepository(self.db)
        matches = MatchRepository(self.db)
        applications = ApplicationRepository(self.db)
        interviews = InterviewRepository(self.db)
        users = UserRepository(self.db)

        resume_list = resumes.list_for_user(user.id)
        analyses = resumes.analyses_for_user(user.id)
        skills = resumes.skills_for_user(user.id)
        gaps = matches.gaps_for_user(user.id)
        match_list = matches.list_for_user(user.id)
        application_list = applications.list_for_user(user.id)
        interview_list = interviews.list_for_user(user.id)
        profile = users.get_profile(user.id)

        skill_counts = Counter(s.normalized for s in skills)
        buckets = Counter()
        for match in match_list:
            low = int(match.overall_score // 20) * 20
            buckets[f"{low}-{min(low + 20, 100)}"] += 1

        funnel = Counter(a.status for a in application_list)

        interview_points = [
            InterviewPerformancePoint(
                date=i.completed_at.strftime("%Y-%m-%d"),
                score=float((i.report or {}).get("overall_score", 0)),
            )
            for i in sorted(
                (i for i in interview_list
                 if i.status == "completed" and i.completed_at),
                key=lambda i: i.completed_at,
            )
        ]

        result = DashboardOut(
            resume_count=len(resume_list),
            latest_resume_score=analyses[-1].overall_score if analyses else None,
            profile_completeness=self._profile_completeness(user, profile, resume_list),
            top_skills=[
                SkillCoverageItem(skill=s, count=c)
                for s, c in skill_counts.most_common(10)
            ],
            skill_gap_count=len(gaps),
            top_gaps=[g.skill for g in gaps if g.priority == "critical"][:5],
            target_roles=list(profile.target_roles or []) if profile else [],
            job_count=len(JobRepository(self.db).list_for_user(user.id)),
            match_count=len(match_list),
            best_match_score=max((m.overall_score for m in match_list), default=None),
            application_count=len(application_list),
            score_history=[
                ScorePoint(date=a.created_at.strftime("%Y-%m-%d"), score=a.overall_score)
                for a in analyses
            ],
            match_distribution=[
                MatchDistributionBucket(bucket=b, count=c)
                for b, c in sorted(buckets.items())
            ],
            application_funnel=[
                FunnelStage(status=s, count=funnel.get(s, 0))
                for s in ("saved", "applied", "screening", "interview", "offer",
                          "rejected", "withdrawn")
            ],
            interview_performance=interview_points,
        )
        cache.set(cache_key, result.model_dump(),
                  ttl_seconds=get_settings().cache_ttl_seconds)
        return result

    @staticmethod
    def _profile_completeness(user: User, profile, resume_list) -> float:
        checks = [
            bool(user.full_name),
            bool(profile and profile.headline),
            bool(profile and profile.location),
            bool(profile and profile.target_roles),
            bool(profile and profile.experience_years is not None),
            bool(resume_list),
        ]
        return round(sum(checks) / len(checks) * 100, 0)

    def admin_stats(self) -> AdminStats:
        cache = get_cache()
        processing = cache.get("metrics:resume_processing") or {}
        return AdminStats(
            total_users=UserRepository(self.db).count(),
            total_resumes=ResumeRepository(self.db).count(),
            total_jobs=JobRepository(self.db).count(),
            total_matches=MatchRepository(self.db).count(),
            total_interviews=InterviewRepository(self.db).count(),
            ai_requests=int(cache.get("metrics:ai_requests") or 0),
            ai_errors=int(cache.get("metrics:ai_errors") or 0),
            avg_resume_processing_seconds=(
                round(processing["total"] / processing["count"], 2)
                if processing.get("count") else None
            ),
        )

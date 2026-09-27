from fastapi import APIRouter

from app.api.v1 import (
    applications,
    auth,
    dashboard,
    interviews,
    jobs,
    profile,
    resumes,
    skills,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(resumes.router)
api_router.include_router(jobs.router)
api_router.include_router(skills.router)
api_router.include_router(interviews.router)
api_router.include_router(applications.router)
api_router.include_router(dashboard.router)

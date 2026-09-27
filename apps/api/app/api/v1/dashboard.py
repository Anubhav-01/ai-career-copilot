from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import AdminStats, DashboardOut
from app.services.dashboard_service import DashboardService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> DashboardOut:
    return DashboardService(db).get(user)


@router.get("/admin/stats", response_model=AdminStats)
def admin_stats(
    _: User = Depends(get_admin_user), db: Session = Depends(get_db)
) -> AdminStats:
    return DashboardService(db).admin_stats()

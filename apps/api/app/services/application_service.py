import uuid

from sqlalchemy.orm import Session

from app.core.cache import get_cache
from app.core.errors import NotFoundError, ValidationFailedError
from app.models.application import APPLICATION_STATUSES, Application
from app.models.user import User
from app.repositories.application import ApplicationRepository
from app.schemas.application import ApplicationCreate, ApplicationUpdate


class ApplicationService:
    def __init__(self, db: Session):
        self.db = db
        self.applications = ApplicationRepository(db)

    def create(self, user: User, payload: ApplicationCreate) -> Application:
        if payload.status not in APPLICATION_STATUSES:
            raise ValidationFailedError(
                f"Invalid status. Allowed: {', '.join(APPLICATION_STATUSES)}"
            )
        application = self.applications.add(Application(
            user_id=user.id,
            **payload.model_dump(),
        ))
        get_cache().delete_prefix(f"dashboard:{user.id}")
        return application

    def list(self, user: User) -> list[Application]:
        return self.applications.list_for_user(user.id)

    def update(self, user: User, application_id: uuid.UUID,
               payload: ApplicationUpdate) -> Application:
        application = self._get_owned(user, application_id)
        updates = payload.model_dump(exclude_unset=True)
        if "status" in updates and updates["status"] not in APPLICATION_STATUSES:
            raise ValidationFailedError(
                f"Invalid status. Allowed: {', '.join(APPLICATION_STATUSES)}"
            )
        for key, value in updates.items():
            setattr(application, key, value)
        self.db.flush()
        get_cache().delete_prefix(f"dashboard:{user.id}")
        return application

    def delete(self, user: User, application_id: uuid.UUID) -> None:
        application = self._get_owned(user, application_id)
        self.applications.soft_delete(application)
        get_cache().delete_prefix(f"dashboard:{user.id}")

    def _get_owned(self, user: User, application_id: uuid.UUID) -> Application:
        application = self.applications.get_for_user(application_id, user.id)
        if application is None:
            raise NotFoundError("Application not found.")
        return application

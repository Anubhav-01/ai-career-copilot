import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: str,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        meta: dict | None = None,
    ) -> None:
        self.db.add(AuditLog(
            user_id=user_id, action=action, resource_type=resource_type,
            resource_id=resource_id, meta=meta,
        ))
        self.db.flush()

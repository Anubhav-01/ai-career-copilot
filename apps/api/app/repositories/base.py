"""Generic repository with user-scoped access and soft deletion.

Every query that touches user-owned resources filters by user_id at the
repository level, so authorization cannot be forgotten in services.
"""
import uuid
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.db.base import Base, SoftDeleteMixin, utcnow

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def _query(self):
        query = self.db.query(self.model)
        if issubclass(self.model, SoftDeleteMixin):
            query = query.filter(self.model.deleted_at.is_(None))
        return query

    def get(self, id: uuid.UUID) -> ModelT | None:
        return self._query().filter(self.model.id == id).first()

    def get_for_user(self, id: uuid.UUID, user_id: uuid.UUID) -> ModelT | None:
        return (
            self._query()
            .filter(self.model.id == id, self.model.user_id == user_id)
            .first()
        )

    def list_for_user(self, user_id: uuid.UUID) -> list[ModelT]:
        return (
            self._query()
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .all()
        )

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        return obj

    def soft_delete(self, obj: ModelT) -> None:
        if isinstance(obj, SoftDeleteMixin):
            obj.deleted_at = utcnow()
            self.db.flush()
        else:
            self.hard_delete(obj)

    def hard_delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()

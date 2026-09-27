import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.models.user import Profile, RefreshToken, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: uuid.UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def create(self, email: str, password_hash: str, full_name: str) -> User:
        user = User(email=email.lower(), password_hash=password_hash, full_name=full_name)
        self.db.add(user)
        self.db.flush()
        return user

    def count(self) -> int:
        return self.db.query(User).count()

    # --- profile ---

    def get_profile(self, user_id: uuid.UUID) -> Profile | None:
        return self.db.query(Profile).filter(Profile.user_id == user_id).first()

    def upsert_profile(self, user_id: uuid.UUID, **fields) -> Profile:
        profile = self.get_profile(user_id)
        if profile is None:
            profile = Profile(user_id=user_id)
            self.db.add(profile)
        for key, value in fields.items():
            if value is not None:
                setattr(profile, key, value)
        self.db.flush()
        return profile

    # --- refresh tokens ---

    def store_refresh_token(
        self, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id, token_hash=token_hash,
            expires_at=expires_at, created_at=utcnow(),
        )
        self.db.add(token)
        self.db.flush()
        return token

    def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        return (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )

    def revoke_refresh_token(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        self.db.flush()

    def revoke_all_refresh_tokens(self, user_id: uuid.UUID) -> None:
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        ).update({RefreshToken.revoked_at: datetime.now(timezone.utc)})
        self.db.flush()

    def delete_user(self, user: User) -> None:
        """Hard delete for account removal (GDPR-style)."""
        self.db.delete(user)
        self.db.flush()

from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthenticationError, ConflictError
from app.core.logging import get_logger, log_event
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories.audit import AuditRepository
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest, TokenPair

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.audit = AuditRepository(db)

    def register(self, payload: RegisterRequest) -> tuple[User, TokenPair]:
        if self.users.get_by_email(payload.email):
            raise ConflictError("An account with this email already exists.")
        user = self.users.create(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name.strip(),
        )
        self.users.upsert_profile(user.id)
        tokens = self._issue_tokens(user)
        self.audit.log("user.register", user_id=user.id)
        log_event(logger, "user_registered")
        return user, tokens

    def login(self, email: str, password: str) -> tuple[User, TokenPair]:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Incorrect email or password.")
        if not user.is_active:
            raise AuthenticationError("This account is disabled.")
        tokens = self._issue_tokens(user)
        self.audit.log("user.login", user_id=user.id)
        return user, tokens

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = jwt.decode(
                refresh_token,
                get_settings().jwt_secret,
                algorithms=[get_settings().jwt_algorithm],
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid refresh token.") from exc
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token.")

        stored = self.users.get_refresh_token(hash_token(refresh_token))
        if stored is None or stored.revoked_at is not None:
            raise AuthenticationError("Refresh token has been revoked.")
        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Refresh token has expired.")

        user = self.users.get(stored.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError()

        # Rotation: revoke the used token, issue a fresh pair.
        self.users.revoke_refresh_token(stored)
        return self._issue_tokens(user)

    def logout(self, refresh_token: str) -> None:
        stored = self.users.get_refresh_token(hash_token(refresh_token))
        if stored and stored.revoked_at is None:
            self.users.revoke_refresh_token(stored)

    def change_password(self, user: User, current: str, new: str) -> None:
        if not verify_password(current, user.password_hash):
            raise AuthenticationError("Current password is incorrect.")
        user.password_hash = hash_password(new)
        self.users.revoke_all_refresh_tokens(user.id)
        self.audit.log("user.change_password", user_id=user.id)
        self.db.flush()

    def delete_account(self, user: User, password: str) -> None:
        """Full account deletion: cascades remove resumes, embeddings,
        matches, interviews and applications (privacy requirement)."""
        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Password is incorrect.")
        self.audit.log("user.delete_account", user_id=user.id)
        self.users.delete_user(user)

    def _issue_tokens(self, user: User) -> TokenPair:
        settings = get_settings()
        refresh = create_refresh_token(str(user.id))
        self.users.store_refresh_token(
            user.id,
            hash_token(refresh),
            datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        )
        return TokenPair(
            access_token=create_access_token(str(user.id)), refresh_token=refresh
        )

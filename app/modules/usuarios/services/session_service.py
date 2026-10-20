import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.modules.usuarios.models import LoginAttempt, User, UserSession
from app.modules.usuarios.repository.session_repository import SessionRepository

TOUCH_INTERVAL = timedelta(minutes=1)


def utc_now() -> datetime:
    return datetime.now(UTC)


class SessionService:
    """Sesiones y limite de intentos de login, persistidos solo en PostgreSQL."""

    def __init__(self, db: Session, config: Settings = settings) -> None:
        self.repository = SessionRepository(db)
        self.config = config

    def digest(self, value: str) -> str:
        return hmac.new(
            self.config.secret_key.encode(),
            value.encode(),
            hashlib.sha256,
        ).hexdigest()

    @property
    def idle_timeout(self) -> timedelta:
        return timedelta(minutes=self.config.session_idle_minutes)

    def create(self, user_id: str) -> str:
        now = utc_now()
        self.repository.purge_unusable_sessions(now, now - self.idle_timeout)
        token = secrets.token_urlsafe(32)
        self.repository.add_session(
            UserSession(
                id=str(uuid4()),
                token_digest=self.digest(token),
                user_id=user_id,
                created_at=now,
                last_used_at=now,
                expires_at=now + timedelta(hours=self.config.session_max_hours),
            )
        )
        return token

    def resolve(self, token: str) -> User | None:
        now = utc_now()
        found = self.repository.find_active_user(
            self.digest(token),
            now,
            now - self.idle_timeout,
        )
        if found is None:
            return None
        session, user = found
        self.repository.touch(session.id, now, now - TOUCH_INTERVAL)
        return user

    def revoke(self, token: str, reason: str = "logout") -> None:
        self.repository.revoke(self.digest(token), utc_now(), reason)

    def revoke_all_for_user(self, user_id: str, reason: str) -> None:
        self.repository.revoke_all_for_user(user_id, utc_now(), reason)

    def _lockout_window_start(self) -> datetime:
        return utc_now() - timedelta(minutes=self.config.login_lockout_minutes)

    def login_is_locked(self, email: str) -> bool:
        attempts = self.repository.count_failed_attempts(
            self.digest(email),
            self._lockout_window_start(),
        )
        return attempts >= self.config.login_max_failed_attempts

    def record_failed_login(self, email: str) -> None:
        self.repository.purge_failed_attempts(self._lockout_window_start())
        self.repository.add_failed_attempt(
            LoginAttempt(
                id=str(uuid4()),
                email_digest=self.digest(email),
                attempted_at=utc_now(),
            )
        )

    def clear_failed_logins(self, email: str) -> None:
        self.repository.clear_failed_attempts(self.digest(email))

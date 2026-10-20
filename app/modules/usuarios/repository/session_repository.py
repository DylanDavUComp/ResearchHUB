from datetime import datetime

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.modules.usuarios.models import LoginAttempt, User, UserSession


class SessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_session(self, session: UserSession) -> None:
        self.db.add(session)
        self.db.commit()

    def find_active_user(
        self,
        token_digest: str,
        now: datetime,
        idle_since: datetime,
    ) -> tuple[UserSession, User] | None:
        row = self.db.execute(
            select(UserSession, User)
            .join(User, User.id == UserSession.user_id)
            .where(
                UserSession.token_digest == token_digest,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
                UserSession.last_used_at > idle_since,
            )
        ).first()
        return None if row is None else (row[0], row[1])

    def touch(self, session_id: str, now: datetime, touched_before: datetime) -> None:
        # Una escritura por minuto como maximo para no cargar la base en cada request.
        result = self.db.execute(
            update(UserSession)
            .where(
                UserSession.id == session_id,
                UserSession.last_used_at < touched_before,
            )
            .values(last_used_at=now)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount:  # type: ignore[attr-defined]
            self.db.commit()

    def revoke(self, token_digest: str, now: datetime, reason: str) -> None:
        self.db.execute(
            update(UserSession)
            .where(
                UserSession.token_digest == token_digest,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=now, revoked_reason=reason)
            .execution_options(synchronize_session=False)
        )
        self.db.commit()

    def revoke_all_for_user(self, user_id: str, now: datetime, reason: str) -> None:
        self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=now, revoked_reason=reason)
            .execution_options(synchronize_session=False)
        )
        self.db.commit()

    def purge_unusable_sessions(self, now: datetime, idle_since: datetime) -> None:
        self.db.execute(
            delete(UserSession)
            .where(
                or_(
                    UserSession.expires_at <= now,
                    UserSession.last_used_at <= idle_since,
                    UserSession.revoked_at.is_not(None),
                )
            )
            .execution_options(synchronize_session=False)
        )
        self.db.commit()

    def count_failed_attempts(self, email_digest: str, since: datetime) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(LoginAttempt)
                .where(
                    LoginAttempt.email_digest == email_digest,
                    LoginAttempt.attempted_at > since,
                )
            )
            or 0
        )

    def add_failed_attempt(self, attempt: LoginAttempt) -> None:
        self.db.add(attempt)
        self.db.commit()

    def clear_failed_attempts(self, email_digest: str) -> None:
        self.db.execute(
            delete(LoginAttempt).where(LoginAttempt.email_digest == email_digest)
        )
        self.db.commit()

    def purge_failed_attempts(self, before: datetime) -> None:
        self.db.execute(
            delete(LoginAttempt)
            .where(LoginAttempt.attempted_at <= before)
            .execution_options(synchronize_session=False)
        )
        self.db.commit()

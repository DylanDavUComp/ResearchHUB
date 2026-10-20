from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserSession(Base):
    """Sesion institucional compartida por ResearchHUB y ResearchOS.

    Solo se guarda la huella HMAC del identificador; el valor real vive
    unicamente en la cookie HttpOnly del navegador.
    """

    __tablename__ = "sesiones"
    __table_args__ = (
        UniqueConstraint("token_digest", name="uq_sesiones_token_digest"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    token_digest: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_reason: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

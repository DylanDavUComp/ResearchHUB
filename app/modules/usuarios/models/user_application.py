from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.usuarios.models.user import User

ApplicationCode = Literal["research_hub", "research_os"]

APPLICATION_CODES: tuple[ApplicationCode, ...] = ("research_hub", "research_os")

APPLICATION_NAMES: dict[ApplicationCode, str] = {
    "research_hub": "ResearchHUB",
    "research_os": "ResearchOS",
}


class UserApplication(Base):
    """Acceso de un usuario a una aplicacion que comparte el login institucional."""

    __tablename__ = "usuario_aplicaciones"
    __table_args__ = (
        CheckConstraint(
            "application IN ('research_hub', 'research_os')",
            name="ck_usuario_aplicaciones_application",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )

    application: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
        index=True,
    )

    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    granted_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="application_grants",
        foreign_keys=[user_id],
    )

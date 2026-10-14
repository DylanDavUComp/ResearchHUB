from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(160))
    summary: Mapped[str] = mapped_column(String(280))
    body: Mapped[str] = mapped_column(Text, default="")
    link_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_alt: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", index=True)
    author_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __mapper_args__ = {"version_id_col": version}


class AnnouncementAuditEvent(Base):
    """Immutable trail; it survives the deletion of a draft announcement."""

    __tablename__ = "announcement_audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    announcement_id: Mapped[str] = mapped_column(String(36), index=True)
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    actor_role: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(20))
    from_status: Mapped[str] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

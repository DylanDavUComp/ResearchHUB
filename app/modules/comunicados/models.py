from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(160))
    summary: Mapped[str] = mapped_column(String(280))
    # Texto plano derivado de `content`, para busquedas y clientes sin bloques.
    body: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
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


class AnnouncementAsset(Base):
    """Imagen o documento subido a un comunicado (ADR-006).

    Un archivo sin comunicado es una subida en curso: se vincula al guardar y, si
    nunca se guarda, se elimina al dia siguiente.
    """

    __tablename__ = "announcement_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    announcement_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("announcements.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(20))
    content_type: Mapped[str] = mapped_column(String(80))
    filename: Mapped[str] = mapped_column(String(200))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    data: Mapped[bytes] = deferred(mapped_column(LargeBinary))
    uploaded_by: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )

    # Ordena el INSERT del comunicado antes de vincular sus archivos.
    announcement: Mapped[Announcement | None] = relationship()

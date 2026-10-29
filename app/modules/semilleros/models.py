from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class SemilleroApplication(Base):
    __tablename__ = "semillero_applications"
    __table_args__ = (UniqueConstraint("student_id", "create_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True
    )
    reviewer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    create_key: Mapped[str] = mapped_column(String(100))
    create_hash: Mapped[str] = mapped_column(String(64))
    semillero_name: Mapped[str] = mapped_column(String(160))
    project_title: Mapped[str] = mapped_column(String(220))
    program: Mapped[str] = mapped_column(String(160))
    current_stage: Mapped[int] = mapped_column(Integer, default=2)
    version: Mapped[int] = mapped_column(Integer, default=1)
    registration_reference: Mapped[str | None] = mapped_column(String(160))
    semester: Mapped[int | None] = mapped_column(Integer)
    plan_summary: Mapped[str | None] = mapped_column(Text)
    plan_deliverables: Mapped[str | None] = mapped_column(Text)
    planned_hours: Mapped[int | None] = mapped_column(Integer)
    plan_status: Mapped[str] = mapped_column(String(20), default="NOT_SUBMITTED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    history: Mapped[list["SemilleroEvent"]] = relationship(
        back_populates="application", order_by="SemilleroEvent.created_at"
    )

    @property
    def completed_stages(self) -> list[int]:
        return list(range(1, min(self.current_stage, 5)))


class SemilleroEvent(Base):
    __tablename__ = "semillero_events"
    __table_args__ = (UniqueConstraint("application_id", "idempotency_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    application_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("semillero_applications.id", ondelete="RESTRICT"),
        index=True,
    )
    actor_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(30))
    from_stage: Mapped[int] = mapped_column(Integer)
    to_stage: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String(500), default="")
    idempotency_key: Mapped[str] = mapped_column(String(100))
    request_hash: Mapped[str] = mapped_column(String(64))
    result_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    application: Mapped[SemilleroApplication] = relationship(back_populates="history")

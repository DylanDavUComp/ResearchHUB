from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class DegreeWorkModality(Base):
    __tablename__ = "degree_work_modalities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    is_homologatable: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", index=True)
    initial_semester: Mapped[int] = mapped_column(Integer, nullable=True)
    duration_label: Mapped[str] = mapped_column(String(120), default="Por definir")
    min_participants: Mapped[int] = mapped_column(Integer, default=1)
    max_participants: Mapped[int] = mapped_column(Integer, default=1)
    requirements: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    evaluation_criteria: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    workflow_steps: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class DegreeWorkCase(Base):
    __tablename__ = "degree_work_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True
    )
    modality_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("degree_work_modalities.id", ondelete="RESTRICT")
    )
    modality_code: Mapped[str] = mapped_column(String(80), index=True)
    modality_name: Mapped[str] = mapped_column(String(160))
    modality_version: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(220))
    program: Mapped[str] = mapped_column(String(160), index=True)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    current_step_index: Mapped[int] = mapped_column(Integer, default=0)
    workflow_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    assigned_teacher_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    history: Mapped[list["DegreeWorkAuditEvent"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="DegreeWorkAuditEvent.created_at",
    )

    @property
    def current_step(self) -> dict[str, Any] | None:
        if self.current_step_index >= len(self.workflow_snapshot):
            return None
        return self.workflow_snapshot[self.current_step_index]

    @property
    def progress_percent(self) -> int:
        if not self.workflow_snapshot:
            return 0
        if self.status == "CLOSED":
            return 100
        return round(self.current_step_index * 100 / len(self.workflow_snapshot))


class DegreeWorkAuditEvent(Base):
    __tablename__ = "degree_work_audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("degree_work_cases.id", ondelete="CASCADE"),
        index=True,
    )
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    actor_role: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(30))
    step_code: Mapped[str] = mapped_column(String(80))
    from_status: Mapped[str] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30))
    comment: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    case: Mapped[DegreeWorkCase] = relationship(back_populates="history")

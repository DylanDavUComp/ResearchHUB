from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RoleName = Literal[
    "Estudiante",
    "Docente",
    "Director de programa",
    "Administrador",
    "Super administrador",
]


class WorkflowStep(BaseModel):
    code: str = Field(min_length=2, max_length=80, pattern=r"^[A-Z0-9_]+$")
    name: str = Field(min_length=2, max_length=160)
    step_type: Literal[
        "FORM",
        "DOCUMENT",
        "VALIDATION",
        "APPROVAL",
        "ASSIGNMENT",
        "ACTIVITY",
        "EVALUATION",
        "CALCULATION",
        "REGISTRATION",
        "CLOSURE",
    ]
    responsible_roles: list[RoleName] = Field(min_length=1)
    is_decision: bool = False


class EvaluationCriterion(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    weight: float = Field(ge=0, le=100)


class ModalityBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=2000)
    is_homologatable: bool = False
    initial_semester: int | None = Field(default=None, ge=1, le=20)
    duration_label: str = Field(default="Por definir", max_length=120)
    min_participants: int = Field(default=1, ge=1, le=20)
    max_participants: int = Field(default=1, ge=1, le=20)
    requirements: list[dict[str, str]] = Field(default_factory=list)
    evaluation_criteria: list[EvaluationCriterion] = Field(default_factory=list)
    workflow_steps: list[WorkflowStep] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_participant_range(self) -> "ModalityBase":
        if self.min_participants > self.max_participants:
            raise ValueError("El mínimo de participantes no puede superar el máximo.")
        return self


class ModalityCreate(ModalityBase):
    code: str = Field(min_length=2, max_length=80, pattern=r"^[A-Z0-9_]+$")


class ModalityUpdate(ModalityBase):
    pass


class ModalityRead(ModalityBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    status: str
    version: int
    created_at: datetime
    updated_at: datetime


class CaseCreate(BaseModel):
    modality_code: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=5, max_length=220)
    program: str = Field(min_length=2, max_length=160)

    @field_validator("modality_code")
    @classmethod
    def normalize_modality_code(cls, value: str) -> str:
        return value.strip().upper()


class CaseTransitionCreate(BaseModel):
    action: Literal["COMPLETE", "RETURN", "REJECT"]
    comment: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def require_comment_for_negative_actions(self) -> "CaseTransitionCreate":
        if self.action in {"RETURN", "REJECT"} and not self.comment.strip():
            raise ValueError("Devolver o rechazar exige una observación.")
        return self


class CaseAssignmentCreate(BaseModel):
    teacher_id: str = Field(min_length=1, max_length=36)


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str
    actor_role: str
    action: str
    step_code: str
    from_status: str
    to_status: str
    comment: str
    created_at: datetime


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    modality_id: str
    modality_code: str
    modality_name: str
    modality_version: int
    title: str
    program: str
    status: str
    current_step_index: int
    current_step: dict[str, object] | None
    progress_percent: int
    workflow_snapshot: list[dict[str, object]]
    assigned_teacher_id: str | None
    history: list[AuditEventRead]
    created_at: datetime
    updated_at: datetime


class PaginatedCases(BaseModel):
    data: list[CaseRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int

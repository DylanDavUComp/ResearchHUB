from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApplicationCreate(BaseModel):
    semillero_name: str = Field(min_length=3, max_length=160)
    project_title: str = Field(min_length=5, max_length=220)
    program: str = Field(min_length=2, max_length=160)

    @field_validator("semillero_name", "project_title", "program")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío.")
        return value


class VersionedCommand(BaseModel):
    expected_version: int = Field(ge=1)


class RegistrationCommand(VersionedCommand):
    reference: str = Field(min_length=3, max_length=160)

    @field_validator("reference")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La referencia no puede estar vacía.")
        return value


class ReviewerAssignmentCommand(VersionedCommand):
    reviewer_id: str = Field(min_length=1, max_length=36)


class ValidationCommand(VersionedCommand):
    eligible: bool
    semester: int = Field(ge=1, le=20)
    comment: str = Field(min_length=5, max_length=500)

    @field_validator("comment")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El comentario no puede estar vacío.")
        return value


class PlanCommand(VersionedCommand):
    summary: str = Field(min_length=20, max_length=3000)
    deliverables: str = Field(min_length=10, max_length=2000)
    planned_hours: int = Field(ge=60, le=1000)

    @field_validator("summary", "deliverables")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío.")
        return value


class PlanDecisionCommand(VersionedCommand):
    approved: bool
    comment: str = Field(min_length=5, max_length=500)

    @field_validator("comment")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El comentario no puede estar vacío.")
        return value


class DirectorRead(BaseModel):
    id: str
    name: str


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str
    action: str
    from_stage: int
    to_stage: int
    comment: str
    created_at: datetime


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    reviewer_id: str | None
    semillero_name: str
    project_title: str
    program: str
    current_stage: int
    completed_stages: list[int]
    version: int
    registration_reference: str | None
    semester: int | None
    plan_summary: str | None
    plan_deliverables: str | None
    planned_hours: int | None
    plan_status: str
    history: list[EventRead]
    created_at: datetime
    updated_at: datetime


class PaginatedApplications(BaseModel):
    data: list[ApplicationRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int

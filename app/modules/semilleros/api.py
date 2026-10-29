from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppError
from app.core.security import get_current_user
from app.modules.semilleros.schemas import (
    ApplicationCreate,
    ApplicationRead,
    DirectorRead,
    PaginatedApplications,
    PlanCommand,
    PlanDecisionCommand,
    RegistrationCommand,
    ReviewerAssignmentCommand,
    ValidationCommand,
)
from app.modules.semilleros.services import SemilleroService
from app.modules.usuarios.models import User

router = APIRouter(prefix="/semillero-applications", tags=["semilleros"])
user_dependency = Annotated[User, Depends(get_current_user)]
db_dependency = Annotated[Session, Depends(get_db)]
key_dependency = Annotated[
    str, Header(alias="Idempotency-Key", min_length=8, max_length=100)
]


def service(db: db_dependency) -> SemilleroService:
    return SemilleroService(db)


service_dependency = Annotated[SemilleroService, Depends(service)]


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    actor: user_dependency,
    service: service_dependency,
    key: key_dependency,
) -> ApplicationRead:
    try:
        return ApplicationRead.model_validate(service.create(payload, actor, key))
    except PermissionError as exc:
        raise AppError("semillero.forbidden", str(exc), 403) from None


@router.get("", response_model=PaginatedApplications)
def list_applications(
    actor: user_dependency,
    service: service_dependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedApplications:
    try:
        return service.list(actor, page, page_size)
    except PermissionError as exc:
        raise AppError("semillero.forbidden", str(exc), 403) from None


@router.get("/reviewers", response_model=list[DirectorRead])
def search_reviewers(
    actor: user_dependency,
    db: db_dependency,
    q: Annotated[str, Query(max_length=80)] = "",
) -> list[DirectorRead]:
    if actor.role != "Super administrador":
        raise AppError("semillero.forbidden", "No puedes consultar directores.", 403)
    statement = select(User).where(
        User.role == "Director de programa", User.status == "Activo"
    )
    if q.strip():
        statement = statement.where(User.name.ilike(f"%{q.strip()}%"))
    directors = db.scalars(statement.order_by(User.name, User.id).limit(20)).all()
    return [DirectorRead(id=person.id, name=person.name) for person in directors]


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(
    application_id: str,
    actor: user_dependency,
    service: service_dependency,
) -> ApplicationRead:
    try:
        return ApplicationRead.model_validate(service.get(application_id, actor))
    except PermissionError as exc:
        raise AppError("semillero.forbidden", str(exc), 403) from None


@router.post("/{application_id}/register", response_model=ApplicationRead)
def register_application(
    application_id: str,
    payload: RegistrationCommand,
    actor: user_dependency,
    service: service_dependency,
    key: key_dependency,
) -> ApplicationRead:
    try:
        return ApplicationRead.model_validate(
            service.register(application_id, payload, actor, key)
        )
    except PermissionError as exc:
        raise AppError("semillero.forbidden", str(exc), 403) from None


@router.post("/{application_id}/reviewer", response_model=ApplicationRead)
def assign_reviewer(
    application_id: str,
    payload: ReviewerAssignmentCommand,
    actor: user_dependency,
    service: service_dependency,
    key: key_dependency,
) -> ApplicationRead:
    try:
        return ApplicationRead.model_validate(
            service.assign_reviewer(application_id, payload, actor, key)
        )
    except PermissionError as exc:
        raise AppError("semillero.forbidden", str(exc), 403) from None


@router.post("/{application_id}/validate", response_model=ApplicationRead)
def validate_application(
    application_id: str,
    payload: ValidationCommand,
    actor: user_dependency,
    service: service_dependency,
    key: key_dependency,
) -> ApplicationRead:
    try:
        return ApplicationRead.model_validate(
            service.validate(application_id, payload, actor, key)
        )
    except PermissionError as exc:
        raise AppError("semillero.forbidden", str(exc), 403) from None


@router.post("/{application_id}/plan", response_model=ApplicationRead)
def submit_plan(
    application_id: str,
    payload: PlanCommand,
    actor: user_dependency,
    service: service_dependency,
    key: key_dependency,
) -> ApplicationRead:
    try:
        return ApplicationRead.model_validate(
            service.submit_plan(application_id, payload, actor, key)
        )
    except PermissionError as exc:
        raise AppError("semillero.forbidden", str(exc), 403) from None


@router.post("/{application_id}/plan-decision", response_model=ApplicationRead)
def decide_plan(
    application_id: str,
    payload: PlanDecisionCommand,
    actor: user_dependency,
    service: service_dependency,
    key: key_dependency,
) -> ApplicationRead:
    try:
        return ApplicationRead.model_validate(
            service.decide_plan(application_id, payload, actor, key)
        )
    except PermissionError as exc:
        raise AppError("semillero.forbidden", str(exc), 403) from None

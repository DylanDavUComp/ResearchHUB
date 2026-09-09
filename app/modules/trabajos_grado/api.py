from collections.abc import Callable
from math import ceil
from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppError
from app.core.security import get_current_user
from app.modules.trabajos_grado.schemas import (
    CaseAssignmentCreate,
    CaseCreate,
    CaseRead,
    CaseTransitionCreate,
    ModalityCreate,
    ModalityRead,
    ModalityUpdate,
    PaginatedCases,
)
from app.modules.trabajos_grado.services import DegreeWorkService
from app.modules.usuarios.models import User

router = APIRouter(tags=["trabajos de grado"])
T = TypeVar("T")

db_dependency = Annotated[Session, Depends(get_db)]
current_user_dependency = Annotated[User, Depends(get_current_user)]


def get_service(db: db_dependency) -> DegreeWorkService:
    return DegreeWorkService(db)


service_dependency = Annotated[DegreeWorkService, Depends(get_service)]


def execute(operation: Callable[[], T]) -> T:
    try:
        return operation()
    except PermissionError as exc:
        raise AppError(
            "degree_work.forbidden",
            str(exc),
            status.HTTP_403_FORBIDDEN,
        ) from None
    except ValueError as exc:
        raise AppError(
            "degree_work.invalid_configuration",
            str(exc),
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ) from None


@router.get(
    "/degree-work-modalities",
    response_model=list[ModalityRead],
    summary="Listar modalidades de trabajo de grado",
)
def list_modalities(
    current_user: current_user_dependency,
    service: service_dependency,
    include_inactive: bool = False,
) -> list[ModalityRead]:
    if include_inactive and current_user.role not in {
        "Administrador",
        "Super administrador",
    }:
        raise AppError(
            "degree_work.forbidden",
            "Tu rol no permite consultar modalidades no publicadas.",
            status.HTTP_403_FORBIDDEN,
        )
    return [
        ModalityRead.model_validate(item)
        for item in service.list_modalities(include_inactive)
    ]


@router.post(
    "/degree-work-modalities",
    response_model=ModalityRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear modalidad en borrador",
)
def create_modality(
    payload: ModalityCreate,
    current_user: current_user_dependency,
    service: service_dependency,
) -> ModalityRead:
    return ModalityRead.model_validate(
        execute(lambda: service.create_modality(payload, current_user))
    )


@router.patch(
    "/degree-work-modalities/{modality_id}",
    response_model=ModalityRead,
    summary="Editar modalidad en borrador",
)
def update_modality(
    modality_id: str,
    payload: ModalityUpdate,
    current_user: current_user_dependency,
    service: service_dependency,
) -> ModalityRead:
    return ModalityRead.model_validate(
        execute(lambda: service.update_modality(modality_id, payload, current_user))
    )


@router.delete(
    "/degree-work-modalities/{modality_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar modalidad en borrador sin uso",
)
def delete_modality(
    modality_id: str,
    current_user: current_user_dependency,
    service: service_dependency,
) -> Response:
    execute(lambda: service.delete_modality(modality_id, current_user))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/degree-work-modalities/{modality_id}/publication",
    response_model=ModalityRead,
    summary="Publicar modalidad",
)
def publish_modality(
    modality_id: str,
    current_user: current_user_dependency,
    service: service_dependency,
) -> ModalityRead:
    return ModalityRead.model_validate(
        execute(lambda: service.publish_modality(modality_id, current_user))
    )


@router.post(
    "/degree-work-modalities/{modality_id}/retirement",
    response_model=ModalityRead,
    summary="Retirar modalidad",
)
def retire_modality(
    modality_id: str,
    current_user: current_user_dependency,
    service: service_dependency,
) -> ModalityRead:
    return ModalityRead.model_validate(
        execute(lambda: service.retire_modality(modality_id, current_user))
    )


@router.get(
    "/degree-work-cases",
    response_model=PaginatedCases,
    summary="Listar casos según alcance del usuario",
)
def list_cases(
    current_user: current_user_dependency,
    service: service_dependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedCases:
    cases = [
        CaseRead.model_validate(item)
        for item in execute(lambda: service.list_cases(current_user))
    ]
    total_items = len(cases)
    start = (page - 1) * page_size
    return PaginatedCases(
        data=cases[start : start + page_size],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=ceil(total_items / page_size) if total_items else 0,
    )


@router.post(
    "/degree-work-cases",
    response_model=CaseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear caso de trabajo de grado",
)
def create_case(
    payload: CaseCreate,
    current_user: current_user_dependency,
    service: service_dependency,
) -> CaseRead:
    return CaseRead.model_validate(
        execute(lambda: service.create_case(payload, current_user))
    )


@router.get(
    "/degree-work-cases/{case_id}",
    response_model=CaseRead,
    summary="Consultar caso de trabajo de grado",
)
def get_case(
    case_id: str,
    current_user: current_user_dependency,
    service: service_dependency,
) -> CaseRead:
    return CaseRead.model_validate(
        execute(lambda: service.get_case(case_id, current_user))
    )


@router.post(
    "/degree-work-cases/{case_id}/assignments",
    response_model=CaseRead,
    summary="Asignar docente al caso",
)
def assign_teacher(
    case_id: str,
    payload: CaseAssignmentCreate,
    current_user: current_user_dependency,
    service: service_dependency,
) -> CaseRead:
    return CaseRead.model_validate(
        execute(lambda: service.assign_teacher(case_id, payload, current_user))
    )


@router.post(
    "/degree-work-cases/{case_id}/transitions",
    response_model=CaseRead,
    summary="Ejecutar transición disponible",
)
def transition_case(
    case_id: str,
    payload: CaseTransitionCreate,
    current_user: current_user_dependency,
    service: service_dependency,
) -> CaseRead:
    return CaseRead.model_validate(
        execute(lambda: service.transition_case(case_id, payload, current_user))
    )

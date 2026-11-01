from math import ceil
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.modules.comunicados.schemas import (
    AnnouncementCreate,
    AnnouncementPublicRead,
    AnnouncementRead,
    AnnouncementUpdate,
    PaginatedAnnouncements,
    PaginatedPublicAnnouncements,
)
from app.modules.comunicados.services import AnnouncementService
from app.modules.usuarios.models import User

router = APIRouter(tags=["comunicados"])

db_dependency = Annotated[Session, Depends(get_db)]
current_user_dependency = Annotated[User, Depends(get_current_user)]
page_dependency = Annotated[int, Query(ge=1, le=1000)]


def get_service(db: db_dependency) -> AnnouncementService:
    return AnnouncementService(db)


service_dependency = Annotated[AnnouncementService, Depends(get_service)]


class VersionedAction(BaseModel):
    version: int = Field(ge=1)


def count_pages(total_items: int, page_size: int) -> int:
    return ceil(total_items / page_size) if total_items else 0


@router.get(
    "/announcements",
    response_model=PaginatedPublicAnnouncements,
    summary="Listar comunicados publicados",
)
def list_published_announcements(
    service: service_dependency,
    page: page_dependency = 1,
    page_size: Annotated[int, Query(ge=1, le=24)] = 6,
) -> PaginatedPublicAnnouncements:
    items, total_items = service.list_published(page, page_size)
    return PaginatedPublicAnnouncements(
        data=[AnnouncementPublicRead.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=count_pages(total_items, page_size),
    )


@router.get(
    "/admin/announcements",
    response_model=PaginatedAnnouncements,
    summary="Listar comunicados para gestión",
)
def list_managed_announcements(
    current_user: current_user_dependency,
    service: service_dependency,
    page: page_dependency = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[
        Literal["DRAFT", "PUBLISHED", "WITHDRAWN"] | None, Query(alias="status")
    ] = None,
) -> PaginatedAnnouncements:
    items, total_items = service.list_for_management(
        current_user, page, page_size, status_filter
    )
    return PaginatedAnnouncements(
        data=[AnnouncementRead.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=count_pages(total_items, page_size),
    )


@router.post(
    "/admin/announcements",
    response_model=AnnouncementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear comunicado en borrador",
)
def create_announcement(
    payload: AnnouncementCreate,
    current_user: current_user_dependency,
    service: service_dependency,
) -> AnnouncementRead:
    return AnnouncementRead.model_validate(service.create(payload, current_user))


@router.patch(
    "/admin/announcements/{announcement_id}",
    response_model=AnnouncementRead,
    summary="Editar comunicado",
)
def update_announcement(
    announcement_id: str,
    payload: AnnouncementUpdate,
    current_user: current_user_dependency,
    service: service_dependency,
) -> AnnouncementRead:
    return AnnouncementRead.model_validate(
        service.update(announcement_id, payload, current_user)
    )


@router.delete(
    "/admin/announcements/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar comunicado",
)
def delete_announcement(
    announcement_id: str,
    current_user: current_user_dependency,
    service: service_dependency,
) -> Response:
    service.delete(announcement_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/admin/announcements/{announcement_id}/publication",
    response_model=AnnouncementRead,
    summary="Publicar comunicado en la portada",
)
def publish_announcement(
    announcement_id: str,
    payload: VersionedAction,
    current_user: current_user_dependency,
    service: service_dependency,
) -> AnnouncementRead:
    return AnnouncementRead.model_validate(
        service.publish(announcement_id, payload.version, current_user)
    )


@router.post(
    "/admin/announcements/{announcement_id}/withdrawal",
    response_model=AnnouncementRead,
    summary="Retirar comunicado de la portada",
)
def withdraw_announcement(
    announcement_id: str,
    payload: VersionedAction,
    current_user: current_user_dependency,
    service: service_dependency,
) -> AnnouncementRead:
    return AnnouncementRead.model_validate(
        service.withdraw(announcement_id, payload.version, current_user)
    )

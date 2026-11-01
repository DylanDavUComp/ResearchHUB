from math import ceil
from typing import Annotated, Any, Literal
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.database import get_db
from app.core.exceptions import AppError
from app.core.security import get_current_user, get_optional_user
from app.modules.comunicados.assets import (
    MAX_DOCUMENT_BYTES,
    AnnouncementAssetService,
    asset_url,
)
from app.modules.comunicados.importer import ImportReport, import_announcements
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
# Archivos de los comunicados: fuera de /api/ para que el navegador pueda guardarlos
# en cache cuando el comunicado esta publicado.
media_router = APIRouter(tags=["comunicados"])

db_dependency = Annotated[Session, Depends(get_db)]
current_user_dependency = Annotated[User, Depends(get_current_user)]
page_dependency = Annotated[int, Query(ge=1, le=1000)]


def get_service(db: db_dependency) -> AnnouncementService:
    return AnnouncementService(db)


service_dependency = Annotated[AnnouncementService, Depends(get_service)]


class VersionedAction(BaseModel):
    version: int = Field(ge=1)


class AssetRead(BaseModel):
    id: str
    url: str
    kind: str
    content_type: str
    filename: str
    size_bytes: int


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
    "/announcements/{announcement_id}",
    response_model=AnnouncementPublicRead,
    summary="Leer un comunicado publicado",
)
def read_published_announcement(
    announcement_id: str, service: service_dependency
) -> AnnouncementPublicRead:
    return AnnouncementPublicRead.model_validate(service.get_published(announcement_id))


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


@router.post(
    "/admin/announcements/import",
    response_model=ImportReport,
    summary="Importar comunicados desde JSON como borradores",
)
def import_announcement_drafts(
    current_user: current_user_dependency,
    db: db_dependency,
    payload: Annotated[Any, Body()],
    dry_run: Annotated[bool, Query()] = True,
) -> ImportReport:
    """Con `dry_run` (por defecto) solo valida y devuelve el informe."""
    return import_announcements(db, payload, current_user, dry_run=dry_run)


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


@router.post(
    "/admin/announcement-assets",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Subir una imagen o un PDF para un comunicado",
)
async def upload_announcement_asset(
    request: Request,
    current_user: current_user_dependency,
    db: db_dependency,
    filename: Annotated[str, Query(min_length=1, max_length=200)],
) -> AssetRead:
    """El archivo llega como cuerpo binario; nunca se confia en su extension."""
    declared = int(request.headers.get("content-length") or 0)
    if declared > MAX_DOCUMENT_BYTES:
        raise AppError(
            "announcements.asset_too_large", "El archivo supera el límite de 5 MB.", 413
        )
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > MAX_DOCUMENT_BYTES:
            raise AppError(
                "announcements.asset_too_large",
                "El archivo supera el límite de 5 MB.",
                413,
            )
    if not data:
        raise AppError("announcements.asset_empty", "El archivo está vacío.", 422)
    service = AnnouncementAssetService(db)
    asset = await run_in_threadpool(service.upload, current_user, filename, bytes(data))
    return AssetRead(
        id=asset.id,
        url=asset_url(asset),
        kind=asset.kind,
        content_type=asset.content_type,
        filename=asset.filename,
        size_bytes=asset.size_bytes,
    )


@media_router.get("/media/announcements/{asset_id}", include_in_schema=False)
def read_announcement_asset(
    asset_id: str,
    db: db_dependency,
    viewer: Annotated[User | None, Depends(get_optional_user)],
) -> Response:
    service = AnnouncementAssetService(db)
    asset = service.get_visible(asset_id, viewer)
    is_public = (
        asset.announcement is not None and asset.announcement.status == "PUBLISHED"
    )
    disposition = "inline" if asset.kind == "image" else "attachment"
    return Response(
        content=asset.data,
        media_type=asset.content_type,
        headers={
            "content-disposition": f"{disposition}; filename*=UTF-8''"
            + quote(asset.filename),
            "cache-control": "public, max-age=86400"
            if is_public
            else "private, no-store",
            "etag": f'"{asset.sha256}"',
        },
    )

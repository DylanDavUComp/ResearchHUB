"""Imagenes y documentos subidos a los comunicados (ADR-006).

El tipo se decide por la firma del contenido, nunca por el nombre ni por el
encabezado del navegador. SVG y HTML no se aceptan: podrian ejecutar scripts.
"""

import hashlib
import logging
import re
import unicodedata
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.modules.comunicados.blocks import ASSET_URL_PREFIX
from app.modules.comunicados.models import Announcement, AnnouncementAsset
from app.modules.usuarios.models import User

logger = logging.getLogger("researchhub.announcements")

MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
MAX_ASSETS_PER_ANNOUNCEMENT = 60
ORPHAN_TTL = timedelta(hours=24)

# (tipo, extension, clase) por firma de archivo.
SIGNATURES: list[tuple[bytes, str, str, str]] = [
    (b"\x89PNG\r\n\x1a\n", "image/png", "png", "image"),
    (b"\xff\xd8\xff", "image/jpeg", "jpg", "image"),
    (b"GIF87a", "image/gif", "gif", "image"),
    (b"GIF89a", "image/gif", "gif", "image"),
    (b"%PDF-", "application/pdf", "pdf", "document"),
]


def detect_type(data: bytes) -> tuple[str, str, str] | None:
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", "webp", "image"
    for signature, content_type, extension, kind in SIGNATURES:
        if data.startswith(signature):
            return content_type, extension, kind
    return None


def safe_filename(name: str, extension: str) -> str:
    """Nombre legible para descargas, sin rutas ni caracteres de control."""
    base = re.split(r"[\\/]", name or "")[-1]
    base = unicodedata.normalize("NFC", base).rsplit(".", 1)[0]
    base = re.sub(r"[^\w .()-]", "", base, flags=re.UNICODE).strip(" .") or "archivo"
    return f"{base[:120]}.{extension}"


def asset_url(asset: AnnouncementAsset) -> str:
    return f"{ASSET_URL_PREFIX}{asset.id}"


class AnnouncementAssetService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upload(self, actor: User, filename: str, data: bytes) -> AnnouncementAsset:
        if actor.role != "Super administrador":
            raise AppError(
                "announcements.forbidden",
                "La gestión de comunicados es exclusiva de superadministradores.",
                403,
            )
        detected = detect_type(data)
        if detected is None:
            raise AppError(
                "announcements.asset_type",
                "Sube una imagen JPG, PNG, WebP o GIF, o un documento PDF.",
                415,
            )
        content_type, extension, kind = detected
        limit = MAX_IMAGE_BYTES if kind == "image" else MAX_DOCUMENT_BYTES
        if len(data) > limit:
            raise AppError(
                "announcements.asset_too_large",
                f"El archivo supera el límite de {limit // (1024 * 1024)} MB para "
                f"{'imágenes' if kind == 'image' else 'documentos PDF'}.",
                413,
            )
        self._purge_orphans()
        asset = AnnouncementAsset(
            id=str(uuid4()),
            kind=kind,
            content_type=content_type,
            filename=safe_filename(filename, extension),
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            data=data,
            uploaded_by=actor.id,
        )
        self.db.add(asset)
        self.db.commit()
        logger.info("announcement_asset_uploaded")
        return asset

    def get_visible(self, asset_id: str, viewer: User | None) -> AnnouncementAsset:
        """Publico si su comunicado esta publicado; si no, solo superadministradores."""
        asset = self.db.get(AnnouncementAsset, asset_id)
        if asset is not None:
            if viewer is not None and viewer.role == "Super administrador":
                return asset
            announcement = (
                self.db.get(Announcement, asset.announcement_id)
                if asset.announcement_id
                else None
            )
            if announcement is not None and announcement.status == "PUBLISHED":
                return asset
        raise AppError("announcements.asset_not_found", "El archivo no existe.", 404)

    def sync(self, announcement: Announcement, referenced: set[str]) -> None:
        """Vincula los archivos usados y elimina los que el comunicado ya no usa."""
        if len(referenced) > MAX_ASSETS_PER_ANNOUNCEMENT:
            raise AppError(
                "announcements.too_many_assets",
                f"Un comunicado admite hasta {MAX_ASSETS_PER_ANNOUNCEMENT} archivos.",
                422,
            )
        assets = {
            asset.id: asset
            for asset in self.db.scalars(
                select(AnnouncementAsset).where(AnnouncementAsset.id.in_(referenced))
            )
        }
        for asset_id in referenced:
            asset = assets.get(asset_id)
            if asset is None:
                raise AppError(
                    "announcements.asset_missing",
                    "Un archivo del comunicado ya no existe. Vuelve a subirlo.",
                    422,
                )
            if asset.announcement_id not in (None, announcement.id):
                raise AppError(
                    "announcements.asset_in_use",
                    "Un archivo pertenece a otro comunicado. Súbelo de nuevo en este.",
                    422,
                )
            asset.announcement = announcement
        self.db.execute(
            delete(AnnouncementAsset).where(
                AnnouncementAsset.announcement_id == announcement.id,
                AnnouncementAsset.id.not_in(referenced),
            )
        )

    def delete_for(self, announcement: Announcement) -> None:
        self.db.execute(
            delete(AnnouncementAsset).where(
                AnnouncementAsset.announcement_id == announcement.id
            )
        )

    def _purge_orphans(self) -> None:
        cutoff = datetime.now(UTC) - ORPHAN_TTL
        self.db.execute(
            delete(AnnouncementAsset).where(
                AnnouncementAsset.announcement_id.is_(None),
                AnnouncementAsset.created_at < cutoff,
            )
        )

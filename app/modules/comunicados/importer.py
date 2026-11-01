"""Importacion de comunicados desde JSON (uno o varios) como borradores.

Acepta un comunicado, una lista o {"announcements": [...]}. Primero se valida todo
y se devuelve un informe; si algun comunicado tiene errores no se crea ninguno,
para que corregir y volver a cargar el mismo archivo no duplique nada. Nada se
publica: cada comunicado queda `Por aprobar`.
"""

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.modules.comunicados.blocks import referenced_asset_ids
from app.modules.comunicados.repository import AnnouncementRepository
from app.modules.comunicados.schemas import AnnouncementCreate
from app.modules.comunicados.services import AnnouncementService
from app.modules.usuarios.models import User

logger = logging.getLogger("researchhub.announcements")

MAX_IMPORT_ITEMS = 50


class AnnouncementImportItem(AnnouncementCreate):
    # Un campo desconocido suele ser un error de quien escribio el JSON.
    model_config = ConfigDict(extra="forbid")


ITEM_ADAPTER: TypeAdapter[AnnouncementImportItem] = TypeAdapter(AnnouncementImportItem)


class ImportIssue(BaseModel):
    field: str
    message: str


class ImportItemReport(BaseModel):
    index: int
    title: str
    category: str | None
    blocks: int
    errors: list[ImportIssue]


class ImportReport(BaseModel):
    dry_run: bool
    total: int
    valid: int
    created: int
    items: list[ImportItemReport]


def extract_items(payload: Any) -> list[Any]:
    if isinstance(payload, dict) and "announcements" in payload:
        payload = payload["announcements"]
    items = payload if isinstance(payload, list) else [payload]
    if not items:
        raise AppError(
            "announcements.import_empty", "El archivo no contiene comunicados.", 422
        )
    if len(items) > MAX_IMPORT_ITEMS:
        raise AppError(
            "announcements.import_too_many",
            f"Carga como máximo {MAX_IMPORT_ITEMS} comunicados por archivo.",
            422,
        )
    return items


def describe_location(location: tuple[int | str, ...], raw: dict[str, Any]) -> str:
    """Ubicacion legible: ('content', 3, 'image', 'alt') -> 'Bloque 4 (image) · alt'."""
    parts = list(location)
    if len(parts) >= 2 and parts[0] == "content" and isinstance(parts[1], int):
        index = parts[1]
        blocks = raw.get("content")
        kind = ""
        if isinstance(blocks, list) and index < len(blocks):
            block = blocks[index]
            if isinstance(block, dict):
                kind = str(block.get("type", ""))
        # Pydantic repite el tipo del bloque como segmento; no aporta informacion.
        rest = ".".join(str(part) for part in parts[2:] if part != kind)
        label = f"Bloque {index + 1}" + (f" ({kind})" if kind else "")
        return label + (f" · {rest}" if rest else "")
    return ".".join(str(part) for part in parts) or "comunicado"


# Mensajes en espanol para los errores de validacion mas comunes.
ERROR_MESSAGES: dict[str, str] = {
    "missing": "Campo obligatorio.",
    "extra_forbidden": "Campo no permitido; revisa el skill de comunicados.",
    "string_too_short": "Debe tener al menos {min_length} caracteres.",
    "string_too_long": "Debe tener como máximo {max_length} caracteres.",
    "too_short": "Debe tener al menos {min_length} elementos.",
    "too_long": "Debe tener como máximo {max_length} elementos.",
    "literal_error": "Valor no permitido. Usa: {expected}.",
    "union_tag_invalid": "Tipo de bloque desconocido. Usa: {expected_tags}.",
    "union_tag_not_found": "Cada bloque necesita el campo type.",
    "string_type": "Debe ser texto.",
    "list_type": "Debe ser una lista.",
    "dict_type": "Debe ser un objeto.",
    "model_type": "Debe ser un objeto.",
    "bool_type": "Debe ser true o false.",
    "bool_parsing": "Debe ser true o false.",
    "int_type": "Debe ser un número entero.",
    "int_parsing": "Debe ser un número entero.",
    "date_from_datetime_parsing": "Fecha no válida; usa AAAA-MM-DD.",
    "date_parsing": "Fecha no válida; usa AAAA-MM-DD.",
    "date_type": "Fecha no válida; usa AAAA-MM-DD.",
    "time_parsing": "Hora no válida; usa HH:MM.",
    "time_type": "Hora no válida; usa HH:MM.",
}


def translate_error(issue: Any) -> str:
    template = ERROR_MESSAGES.get(str(issue.get("type")))
    if template is None:
        return str(issue.get("msg", "")).removeprefix("Value error, ")
    context = issue.get("ctx") or {}
    if context.get("min_length") == 1 and issue.get("type") in {
        "string_too_short",
        "too_short",
    }:
        return "No puede estar vacío."
    try:
        return template.format(**context)
    except (KeyError, IndexError):
        return template.split(" Usa:")[0]


def validate_item(
    index: int, raw: Any
) -> tuple[ImportItemReport, AnnouncementImportItem | None]:
    data = raw if isinstance(raw, dict) else {}
    title = str(data.get("title", "")).strip()
    category = data.get("category")
    blocks = data.get("content")
    report = ImportItemReport(
        index=index,
        title=title or f"Comunicado {index + 1}",
        category=category if isinstance(category, str) else None,
        blocks=len(blocks) if isinstance(blocks, list) else 0,
        errors=[],
    )
    if not isinstance(raw, dict):
        report.errors.append(
            ImportIssue(field="comunicado", message="Debe ser un objeto JSON.")
        )
        return report, None
    try:
        item = ITEM_ADAPTER.validate_python(raw)
    except ValidationError as error:
        report.errors.extend(
            ImportIssue(
                field=describe_location(issue["loc"], raw),
                message=translate_error(issue),
            )
            for issue in error.errors()
        )
        return report, None
    report.blocks = len(item.content or [])
    if referenced_asset_ids(item.content_dump(), item.image_url):
        report.errors.append(
            ImportIssue(
                field="imagenes",
                message="Los archivos subidos se agregan desde el editor, no por JSON.",
            )
        )
        return report, None
    return report, item


def import_announcements(
    db: Session, payload: Any, actor: User, *, dry_run: bool
) -> ImportReport:
    service = AnnouncementService(db)
    service.require_admin(actor)
    repository = AnnouncementRepository(db)
    reports: list[ImportItemReport] = []
    valid: list[AnnouncementImportItem] = []
    seen_titles: set[str] = set()
    for index, raw in enumerate(extract_items(payload)):
        report, item = validate_item(index, raw)
        if item is not None:
            key = item.title.casefold()
            if key in seen_titles:
                report.errors.append(
                    ImportIssue(field="title", message="Título repetido en el archivo.")
                )
            elif repository.exists_with_title(item.title):
                report.errors.append(
                    ImportIssue(
                        field="title",
                        message="Ya existe un comunicado con este título.",
                    )
                )
            else:
                valid.append(item)
            seen_titles.add(key)
        reports.append(report)

    result = ImportReport(
        dry_run=dry_run,
        total=len(reports),
        valid=sum(not report.errors for report in reports),
        created=0,
        items=reports,
    )
    if dry_run:
        return result
    if any(report.errors for report in reports):
        raise AppError(
            "announcements.import_invalid",
            "Hay comunicados con errores; no se creó ninguno. Corrige el archivo.",
            422,
            details={"report": result.model_dump()},
        )
    service.create_many(list(valid), actor)
    result.created = len(valid)
    logger.info("announcement_import_created")
    return result

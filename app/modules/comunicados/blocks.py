"""Contenido enriquecido de un comunicado como bloques validados.

El navegador nunca envia ni recibe HTML: cada bloque es un dato tipado que el
servidor valida y que la portada pinta con nodos DOM. Asi un comunicado puede
tener titulos, listas, imagenes, videos o tablas sin abrir la puerta a scripts.
"""

import json
import re
from datetime import date, time
from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.config import settings

ASSET_URL_PREFIX = "/media/announcements/"
ASSET_URL_PATTERN = re.compile(
    r"^/media/announcements/"
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$"
)
MAX_BLOCKS = 150
MAX_CONTENT_BYTES = 200_000

Mark = Literal["bold", "italic", "underline", "strike", "code"]


def asset_id_from_url(value: str) -> str | None:
    match = ASSET_URL_PATTERN.match(value)
    return match.group(1) if match else None


def validate_image_source(value: str) -> str:
    """Imagen subida al comunicado, en /static/ o en un origen HTTPS autorizado."""
    value = value.strip()
    if asset_id_from_url(value):
        return value
    if value.startswith("/static/") and ".." not in value and "//" not in value:
        return value
    parsed = urlparse(value)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if parsed.scheme == "https" and origin in settings.announcement_image_origin_list:
        return value
    raise ValueError(
        "La imagen debe subirse al comunicado, estar en /static/ o en un dominio "
        "autorizado con HTTPS."
    )


def validate_target_url(value: str) -> str:
    """Destino de un enlace, boton o documento: HTTPS, correo o archivo subido."""
    value = value.strip()
    if asset_id_from_url(value):
        return value
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.netloc:
        return value
    if parsed.scheme == "mailto" and "@" in parsed.path:
        return value
    raise ValueError(
        "Los enlaces deben usar HTTPS, ser un correo (mailto:) o un archivo subido."
    )


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Run(Strict):
    """Fragmento de texto con un mismo formato."""

    text: str = Field(min_length=1, max_length=4000)
    marks: list[Mark] = Field(default_factory=list, max_length=5)
    link: str | None = Field(default=None, max_length=500)

    @field_validator("marks")
    @classmethod
    def unique_marks(cls, value: list[Mark]) -> list[Mark]:
        return sorted(set(value))

    @field_validator("link")
    @classmethod
    def check_link(cls, value: str | None) -> str | None:
        return validate_target_url(value) if value else None


Runs = Annotated[list[Run], Field(min_length=1, max_length=200)]


class ParagraphBlock(Strict):
    type: Literal["paragraph"]
    runs: Runs


class HeadingBlock(Strict):
    type: Literal["heading"]
    level: Literal[2, 3]
    runs: Runs


class ListBlock(Strict):
    type: Literal["list"]
    style: Literal["bullet", "ordered"]
    items: list[Runs] = Field(min_length=1, max_length=60)


class QuoteBlock(Strict):
    type: Literal["quote"]
    runs: Runs
    cite: str = Field(default="", max_length=160)


class CalloutBlock(Strict):
    type: Literal["callout"]
    tone: Literal["info", "success", "warning"]
    title: str = Field(default="", max_length=120)
    runs: list[Run] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def require_text(self) -> "CalloutBlock":
        if not self.title.strip() and not self.runs:
            raise ValueError("El destacado necesita un título o un texto.")
        return self


class DividerBlock(Strict):
    type: Literal["divider"]


class Picture(Strict):
    src: str = Field(min_length=1, max_length=500)
    alt: str = Field(min_length=1, max_length=200)
    caption: str = Field(default="", max_length=300)

    @field_validator("src")
    @classmethod
    def check_src(cls, value: str) -> str:
        return validate_image_source(value)

    @field_validator("alt")
    @classmethod
    def check_alt(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Describe la imagen con un texto alternativo.")
        return value.strip()


class ImageBlock(Picture):
    type: Literal["image"]
    size: Literal["normal", "wide"] = "normal"


class GalleryBlock(Strict):
    type: Literal["gallery"]
    images: list[Picture] = Field(min_length=2, max_length=12)


class VideoBlock(Strict):
    type: Literal["video"]
    provider: Literal["youtube", "vimeo"]
    video_id: str = Field(min_length=6, max_length=20)
    title: str = Field(min_length=3, max_length=160)
    caption: str = Field(default="", max_length=300)

    @model_validator(mode="after")
    def check_video_id(self) -> "VideoBlock":
        pattern = r"[A-Za-z0-9_-]{11}" if self.provider == "youtube" else r"\d{6,12}"
        if not re.fullmatch(pattern, self.video_id):
            raise ValueError("El identificador del video no es válido.")
        return self


class ButtonBlock(Strict):
    type: Literal["button"]
    label: str = Field(min_length=2, max_length=60)
    url: str = Field(min_length=1, max_length=500)
    variant: Literal["primary", "secondary"] = "primary"

    @field_validator("url")
    @classmethod
    def check_url(cls, value: str) -> str:
        return validate_target_url(value)


class FileBlock(Strict):
    type: Literal["file"]
    url: str = Field(min_length=1, max_length=500)
    label: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=200)

    @field_validator("url")
    @classmethod
    def check_url(cls, value: str) -> str:
        return validate_target_url(value)


class TableBlock(Strict):
    type: Literal["table"]
    header: bool = True
    caption: str = Field(default="", max_length=200)
    rows: list[list[Annotated[str, Field(max_length=300)]]] = Field(
        min_length=1, max_length=30
    )

    @model_validator(mode="after")
    def check_shape(self) -> "TableBlock":
        widths = {len(row) for row in self.rows}
        if len(widths) != 1 or not 1 <= widths.pop() <= 8:
            raise ValueError("Cada fila de la tabla debe tener de 1 a 8 columnas.")
        if not any(cell.strip() for row in self.rows for cell in row):
            raise ValueError("La tabla está vacía.")
        return self


class EventBlock(Strict):
    type: Literal["event"]
    start_date: date
    start_time: time | None = None
    end_date: date | None = None
    end_time: time | None = None
    mode: Literal["presencial", "virtual", "hibrido"] = "presencial"
    location: str = Field(default="", max_length=200)
    registration_url: str | None = Field(default=None, max_length=500)

    @field_validator("registration_url")
    @classmethod
    def check_registration(cls, value: str | None) -> str | None:
        return validate_target_url(value) if value and value.strip() else None

    @model_validator(mode="after")
    def check_range(self) -> "EventBlock":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("El evento no puede terminar antes de empezar.")
        return self


Block = Annotated[
    ParagraphBlock
    | HeadingBlock
    | ListBlock
    | QuoteBlock
    | CalloutBlock
    | DividerBlock
    | ImageBlock
    | GalleryBlock
    | VideoBlock
    | ButtonBlock
    | FileBlock
    | TableBlock
    | EventBlock,
    Field(discriminator="type"),
]


def check_content_size(blocks: list[BaseModel]) -> None:
    if len(blocks) > MAX_BLOCKS:
        raise ValueError(f"El comunicado admite como máximo {MAX_BLOCKS} bloques.")
    size = len(json.dumps([block.model_dump(mode="json") for block in blocks]))
    if size > MAX_CONTENT_BYTES:
        raise ValueError("El contenido es demasiado extenso para un comunicado.")


def blocks_from_text(text: str) -> list[dict[str, object]]:
    """Convierte el texto plano historico en parrafos."""
    return [
        {"type": "paragraph", "runs": [{"text": paragraph.strip()}]}
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]


def runs_text(runs: object) -> str:
    if not isinstance(runs, list):
        return ""
    return "".join(str(run.get("text", "")) for run in runs if isinstance(run, dict))


def plain_text(blocks: list[dict[str, object]]) -> str:
    """Texto legible del contenido, para busquedas y clientes que no pintan bloques."""
    parts: list[str] = []
    for block in blocks:
        kind = block.get("type")
        if kind in {"paragraph", "heading", "quote", "callout"}:
            title = str(block.get("title") or "")
            parts.append(
                "\n".join(p for p in (title, runs_text(block.get("runs"))) if p)
            )
        elif kind == "list":
            items = block.get("items")
            if isinstance(items, list):
                parts.append("\n".join(f"- {runs_text(item)}" for item in items))
        elif kind in {"image", "button", "file"}:
            parts.append(str(block.get("caption") or block.get("label") or ""))
        elif kind == "table":
            rows = block.get("rows")
            if isinstance(rows, list):
                parts.append("\n".join(" | ".join(map(str, row)) for row in rows))
    return "\n\n".join(part for part in parts if part.strip())


def referenced_asset_ids(blocks: object, *urls: str | None) -> set[str]:
    """Archivos subidos que el contenido o la portada del comunicado usan."""
    found: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, str):
            asset_id = asset_id_from_url(value)
            if asset_id:
                found.add(asset_id)
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(blocks)
    visit(list(urls))
    return found

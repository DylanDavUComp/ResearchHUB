from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.config import settings

AnnouncementCategory = Literal["NOTICIA", "COMUNICADO", "EVENTO", "CONVOCATORIA"]
AnnouncementStatus = Literal["DRAFT", "PUBLISHED", "WITHDRAWN"]


class AnnouncementContent(BaseModel):
    category: AnnouncementCategory
    title: str = Field(min_length=5, max_length=160)
    summary: str = Field(min_length=10, max_length=280)
    body: str = Field(default="", max_length=6000)
    link_url: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=500)
    image_alt: str | None = Field(default=None, max_length=200)

    @field_validator("title", "summary", "body")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("link_url")
    @classmethod
    def validate_link_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip()
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("El enlace debe ser una URL absoluta con HTTPS.")
        return value

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip()
        if value.startswith("/static/") and ".." not in value and "//" not in value:
            return value
        parsed = urlparse(value)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        allowed_origins = settings.announcement_image_origin_list
        if parsed.scheme == "https" and origin in allowed_origins:
            return value
        raise ValueError(
            "La imagen debe estar en /static/ o en un dominio autorizado con HTTPS."
        )

    @model_validator(mode="after")
    def require_image_alt(self) -> "AnnouncementContent":
        self.image_alt = (self.image_alt or "").strip() or None
        if self.image_url and not self.image_alt:
            raise ValueError("Describe la imagen con un texto alternativo.")
        if not self.image_url:
            self.image_alt = None
        return self


class AnnouncementCreate(AnnouncementContent):
    pass


class AnnouncementUpdate(AnnouncementContent):
    version: int = Field(ge=1)


class AnnouncementPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: AnnouncementCategory
    title: str
    summary: str
    body: str
    link_url: str | None
    image_url: str | None
    image_alt: str | None
    published_at: datetime


class AnnouncementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: AnnouncementCategory
    title: str
    summary: str
    body: str
    link_url: str | None
    image_url: str | None
    image_alt: str | None
    status: AnnouncementStatus
    author_id: str | None
    published_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime


class PaginatedPublicAnnouncements(BaseModel):
    data: list[AnnouncementPublicRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class PaginatedAnnouncements(BaseModel):
    data: list[AnnouncementRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.exceptions import AppError
from app.modules.comunicados.assets import AnnouncementAssetService
from app.modules.comunicados.blocks import referenced_asset_ids
from app.modules.comunicados.models import Announcement, AnnouncementAuditEvent
from app.modules.comunicados.repository import AnnouncementRepository
from app.modules.comunicados.schemas import (
    AnnouncementContent,
    AnnouncementCreate,
    AnnouncementUpdate,
)
from app.modules.usuarios.models import User

# Los comunicados se gestionan solo desde la consola de configuracion general.
ADMIN_ROLES = {"Super administrador"}
# Un comunicado se edita o elimina en cualquier estado; solo se publica lo no publicado.
PUBLISHABLE_STATUSES = {"DRAFT", "WITHDRAWN"}


class AnnouncementService:
    def __init__(self, db: Session) -> None:
        self.repository = AnnouncementRepository(db)
        self.assets = AnnouncementAssetService(db)
        self.db = db

    def list_published(
        self, page: int, page_size: int
    ) -> tuple[list[Announcement], int]:
        return self.repository.list_page(
            page=page, page_size=page_size, status="PUBLISHED"
        )

    def get_published(self, announcement_id: str) -> Announcement:
        announcement = self._get(announcement_id)
        if announcement.status != "PUBLISHED":
            raise AppError("announcements.not_found", "El comunicado no existe.", 404)
        return announcement

    def list_for_management(
        self, actor: User, page: int, page_size: int, status: str | None
    ) -> tuple[list[Announcement], int]:
        self._require_admin(actor)
        return self.repository.list_page(page=page, page_size=page_size, status=status)

    def create(self, payload: AnnouncementCreate, actor: User) -> Announcement:
        self._require_admin(actor)
        announcement = Announcement(
            id=str(uuid4()), status="DRAFT", author_id=actor.id, **self._fields(payload)
        )
        self.assets.sync(announcement, self._references(payload))
        event = self._event(announcement, actor, "CREATE", "DRAFT")
        event.from_status = "NONE"
        return self.repository.save(announcement, event)

    def create_many(
        self, payloads: list[AnnouncementCreate], actor: User
    ) -> list[Announcement]:
        """Crea varios borradores en una sola transaccion: todos o ninguno."""
        self._require_admin(actor)
        created: list[Announcement] = []
        for payload in payloads:
            announcement = Announcement(
                id=str(uuid4()),
                status="DRAFT",
                author_id=actor.id,
                **self._fields(payload),
            )
            event = self._event(announcement, actor, "CREATE", "DRAFT")
            event.from_status = "NONE"
            self.db.add_all([announcement, event])
            created.append(announcement)
        self.db.commit()
        return created

    def require_admin(self, actor: User) -> None:
        self._require_admin(actor)

    def update(
        self, announcement_id: str, payload: AnnouncementUpdate, actor: User
    ) -> Announcement:
        self._require_admin(actor)
        announcement = self._get(announcement_id)
        self._require_version(announcement, payload.version)
        for field, value in self._fields(payload).items():
            setattr(announcement, field, value)
        self.assets.sync(announcement, self._references(payload))
        return self._save(
            announcement,
            self._event(announcement, actor, "UPDATE", announcement.status),
        )

    def publish(self, announcement_id: str, version: int, actor: User) -> Announcement:
        self._require_admin(actor)
        announcement = self._get(announcement_id)
        if announcement.status not in PUBLISHABLE_STATUSES:
            raise AppError(
                "announcements.already_published",
                "El comunicado ya está publicado.",
                409,
            )
        self._require_version(announcement, version)
        event = self._event(announcement, actor, "PUBLISH", "PUBLISHED")
        announcement.status = "PUBLISHED"
        announcement.published_at = datetime.now(UTC)
        return self._save(announcement, event)

    def withdraw(self, announcement_id: str, version: int, actor: User) -> Announcement:
        self._require_admin(actor)
        announcement = self._get(announcement_id)
        if announcement.status != "PUBLISHED":
            raise AppError(
                "announcements.not_published",
                "Solo un comunicado publicado puede retirarse.",
                409,
            )
        self._require_version(announcement, version)
        event = self._event(announcement, actor, "WITHDRAW", "WITHDRAWN")
        announcement.status = "WITHDRAWN"
        return self._save(announcement, event)

    def delete(self, announcement_id: str, actor: User) -> None:
        self._require_admin(actor)
        announcement = self._get(announcement_id)
        self.assets.delete_for(announcement)
        self.repository.delete(
            announcement, self._event(announcement, actor, "DELETE", "DELETED")
        )

    @staticmethod
    def _fields(payload: AnnouncementContent) -> dict[str, object]:
        fields = payload.model_dump(exclude={"content", "version"})
        fields["content"] = payload.content_dump()
        return fields

    @staticmethod
    def _references(payload: AnnouncementContent) -> set[str]:
        return referenced_asset_ids(payload.content_dump(), payload.image_url)

    def _save(
        self, announcement: Announcement, event: AnnouncementAuditEvent
    ) -> Announcement:
        try:
            return self.repository.save(announcement, event)
        except StaleDataError:
            self.db.rollback()
            raise self._conflict() from None

    def _get(self, announcement_id: str) -> Announcement:
        announcement = self.repository.get(announcement_id)
        if announcement is None:
            raise AppError(
                "announcements.not_found",
                "El comunicado no existe.",
                404,
            )
        return announcement

    def _require_version(self, announcement: Announcement, version: int) -> None:
        if announcement.version != version:
            raise self._conflict()

    @staticmethod
    def _conflict() -> AppError:
        return AppError(
            "announcements.version_conflict",
            "Otra persona modificó este comunicado. Recarga la lista e intenta "
            "de nuevo.",
            409,
        )

    @staticmethod
    def _require_admin(actor: User) -> None:
        if actor.role not in ADMIN_ROLES:
            raise AppError(
                "announcements.forbidden",
                "La gestión de comunicados es exclusiva de superadministradores.",
                403,
            )

    @staticmethod
    def _event(
        announcement: Announcement, actor: User, action: str, to_status: str
    ) -> AnnouncementAuditEvent:
        return AnnouncementAuditEvent(
            id=str(uuid4()),
            announcement_id=announcement.id,
            actor_id=actor.id,
            actor_role=actor.role,
            action=action,
            from_status=announcement.status,
            to_status=to_status,
        )

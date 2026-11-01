from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.comunicados.models import Announcement, AnnouncementAuditEvent


class AnnouncementRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, announcement_id: str) -> Announcement | None:
        return self.db.get(Announcement, announcement_id)

    def exists_with_title(self, title: str) -> bool:
        statement = select(Announcement.id).where(Announcement.title == title)
        return self.db.scalar(statement.limit(1)) is not None

    def list_page(
        self, *, page: int, page_size: int, status: str | None = None
    ) -> tuple[list[Announcement], int]:
        statement = select(Announcement)
        count_statement = select(func.count()).select_from(Announcement)
        if status is not None:
            statement = statement.where(Announcement.status == status)
            count_statement = count_statement.where(Announcement.status == status)
        if status == "PUBLISHED":
            statement = statement.order_by(
                Announcement.published_at.desc(), Announcement.id
            )
        else:
            statement = statement.order_by(
                Announcement.updated_at.desc(), Announcement.id
            )
        items = self.db.scalars(
            statement.offset((page - 1) * page_size).limit(page_size)
        )
        return list(items), int(self.db.scalar(count_statement) or 0)

    def save(
        self, announcement: Announcement, event: AnnouncementAuditEvent
    ) -> Announcement:
        self.db.add_all([announcement, event])
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def delete(self, announcement: Announcement, event: AnnouncementAuditEvent) -> None:
        self.db.delete(announcement)
        self.db.add(event)
        self.db.commit()

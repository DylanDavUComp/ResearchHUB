from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.semilleros.models import SemilleroApplication, SemilleroEvent
from app.modules.semilleros.schemas import ApplicationRead


class SemilleroRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(
        self, application_id: str, *, for_update: bool = False
    ) -> SemilleroApplication | None:
        statement = (
            select(SemilleroApplication)
            .where(SemilleroApplication.id == application_id)
            .options(selectinload(SemilleroApplication.history))
        )
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def get_by_create_key(
        self, student_id: str, key: str
    ) -> SemilleroApplication | None:
        return self.db.scalar(
            select(SemilleroApplication)
            .where(SemilleroApplication.student_id == student_id)
            .where(SemilleroApplication.create_key == key)
            .options(selectinload(SemilleroApplication.history))
        )

    def get_event(self, application_id: str, key: str) -> SemilleroEvent | None:
        return self.db.scalar(
            select(SemilleroEvent)
            .where(SemilleroEvent.application_id == application_id)
            .where(SemilleroEvent.idempotency_key == key)
        )

    def list_page(
        self,
        student_id: str | None,
        reviewer_id: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[SemilleroApplication], int]:
        condition = (
            SemilleroApplication.student_id == student_id if student_id else None
        )
        count_statement = select(func.count()).select_from(SemilleroApplication)
        statement = select(SemilleroApplication).options(
            selectinload(SemilleroApplication.history)
        )
        if condition is not None:
            count_statement = count_statement.where(condition)
            statement = statement.where(condition)
        if reviewer_id is not None:
            reviewer_condition = SemilleroApplication.reviewer_id == reviewer_id
            count_statement = count_statement.where(reviewer_condition)
            statement = statement.where(reviewer_condition)
        total = int(self.db.scalar(count_statement) or 0)
        statement = (
            statement.order_by(
                SemilleroApplication.created_at.desc(), SemilleroApplication.id.desc()
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(statement)), total

    def save(
        self, application: SemilleroApplication, event: SemilleroEvent
    ) -> ApplicationRead:
        event.application = application
        self.db.add_all([application, event])
        self.db.flush()
        snapshot = ApplicationRead.model_validate(application)
        event.result_snapshot = snapshot.model_dump(mode="json")
        self.db.commit()
        return snapshot

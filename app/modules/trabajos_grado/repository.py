from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.modules.trabajos_grado.models import (
    DegreeWorkAuditEvent,
    DegreeWorkCase,
    DegreeWorkModality,
)


class DegreeWorkRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_modality(self, modality_id: str) -> DegreeWorkModality | None:
        return self.db.get(DegreeWorkModality, modality_id)

    def get_modality_by_code(self, code: str) -> DegreeWorkModality | None:
        return self.db.scalar(
            select(DegreeWorkModality).where(DegreeWorkModality.code == code)
        )

    def list_modalities(self, include_inactive: bool) -> list[DegreeWorkModality]:
        statement = select(DegreeWorkModality).order_by(DegreeWorkModality.name)
        if not include_inactive:
            statement = statement.where(DegreeWorkModality.status == "ACTIVE")
        return list(self.db.scalars(statement))

    def add_modality(self, modality: DegreeWorkModality) -> DegreeWorkModality:
        self.db.add(modality)
        self.db.commit()
        self.db.refresh(modality)
        return modality

    def save_modality(self, modality: DegreeWorkModality) -> DegreeWorkModality:
        self.db.add(modality)
        self.db.commit()
        self.db.refresh(modality)
        return modality

    def delete_modality(self, modality: DegreeWorkModality) -> None:
        self.db.delete(modality)
        self.db.commit()

    def add_case(self, case: DegreeWorkCase) -> DegreeWorkCase:
        self.db.add(case)
        self.db.commit()
        return self.get_case(case.id)  # type: ignore[return-value]

    def get_case(self, case_id: str) -> DegreeWorkCase | None:
        return self.db.scalar(
            select(DegreeWorkCase)
            .options(selectinload(DegreeWorkCase.history))
            .where(DegreeWorkCase.id == case_id)
        )

    def list_cases_for_student(self, student_id: str) -> list[DegreeWorkCase]:
        return self._list_cases(DegreeWorkCase.student_id == student_id)

    def list_cases_for_teacher(self, teacher_id: str) -> list[DegreeWorkCase]:
        return self._list_cases(DegreeWorkCase.assigned_teacher_id == teacher_id)

    def list_cases(self) -> list[DegreeWorkCase]:
        return self._list_cases()

    def _list_cases(
        self, condition: ColumnElement[bool] | None = None
    ) -> list[DegreeWorkCase]:
        statement = (
            select(DegreeWorkCase)
            .options(selectinload(DegreeWorkCase.history))
            .order_by(DegreeWorkCase.updated_at.desc())
        )
        if condition is not None:
            statement = statement.where(condition)
        return list(self.db.scalars(statement))

    def count_cases_for_modality(self, modality_id: str) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(DegreeWorkCase)
                .where(DegreeWorkCase.modality_id == modality_id)
            )
            or 0
        )

    def save_case(
        self, case: DegreeWorkCase, event: DegreeWorkAuditEvent
    ) -> DegreeWorkCase:
        self.db.add_all([case, event])
        self.db.commit()
        return self.get_case(case.id)  # type: ignore[return-value]

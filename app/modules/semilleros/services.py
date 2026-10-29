import hashlib
import json
from math import ceil
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.modules.semilleros.models import SemilleroApplication, SemilleroEvent
from app.modules.semilleros.repository import SemilleroRepository
from app.modules.semilleros.schemas import (
    ApplicationCreate,
    ApplicationRead,
    PaginatedApplications,
    PlanCommand,
    PlanDecisionCommand,
    RegistrationCommand,
    ReviewerAssignmentCommand,
    ValidationCommand,
)
from app.modules.usuarios.models import User


def body_hash(payload: object) -> str:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")  # type: ignore[attr-defined]
    data = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


class SemilleroService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SemilleroRepository(db)

    def create(
        self, payload: ApplicationCreate, actor: User, key: str
    ) -> ApplicationRead:
        if actor.role != "Estudiante":
            raise PermissionError("Solo un estudiante puede solicitar el ingreso.")
        digest = body_hash(payload)
        existing = self.repository.get_by_create_key(actor.id, key)
        if existing:
            if existing.create_hash != digest:
                raise AppError(
                    "semillero.idempotency_conflict",
                    "La clave ya se usó con otros datos.",
                    422,
                )
            return ApplicationRead.model_validate(existing.history[0].result_snapshot)
        application = SemilleroApplication(
            id=str(uuid4()),
            student_id=actor.id,
            create_key=key,
            create_hash=digest,
            semillero_name=payload.semillero_name.strip(),
            project_title=payload.project_title.strip(),
            program=payload.program.strip(),
            current_stage=2,
            version=1,
        )
        event = self._event(application, actor, "SUBMIT", 1, 2, "", key, digest)
        try:
            return self.repository.save(application, event)
        except IntegrityError:
            self.db.rollback()
            existing = self.repository.get_by_create_key(actor.id, key)
            if existing and existing.create_hash == digest:
                return ApplicationRead.model_validate(
                    existing.history[0].result_snapshot
                )
            raise AppError(
                "semillero.idempotency_conflict",
                "La clave ya se usó con otros datos.",
                422,
            ) from None

    def list(self, actor: User, page: int, page_size: int) -> PaginatedApplications:
        if actor.role == "Estudiante":
            student_id: str | None = actor.id
            reviewer_id: str | None = None
        elif actor.role == "Director de programa":
            student_id = None
            reviewer_id = actor.id
        elif actor.role == "Super administrador":
            student_id = None
            reviewer_id = None
        else:
            raise PermissionError("Tu rol no puede consultar estas solicitudes.")
        items, total = self.repository.list_page(
            student_id, reviewer_id, page, page_size
        )
        return PaginatedApplications(
            data=items,  # type: ignore[arg-type]
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=ceil(total / page_size) if total else 0,
        )

    def get(self, application_id: str, actor: User) -> SemilleroApplication:
        application = self.repository.get(application_id)
        if application is None:
            raise AppError("semillero.not_found", "La solicitud no existe.", 404)
        self._can_read(application, actor)
        return application

    def register(
        self, application_id: str, payload: RegistrationCommand, actor: User, key: str
    ) -> ApplicationRead:
        return self._advance(
            application_id,
            payload,
            actor,
            key,
            "REGISTER",
            2,
            3,
            registration_reference=payload.reference.strip(),
        )

    def assign_reviewer(
        self,
        application_id: str,
        payload: ReviewerAssignmentCommand,
        actor: User,
        key: str,
    ) -> ApplicationRead:
        if actor.role != "Super administrador":
            raise PermissionError(
                "Solo el superadministrador puede asignar un director."
            )
        reviewer = self.db.get(User, payload.reviewer_id)
        if (
            reviewer is None
            or reviewer.role != "Director de programa"
            or reviewer.status != "Activo"
        ):
            raise AppError(
                "semillero.invalid_reviewer",
                "Selecciona un director de programa activo.",
                422,
            )
        application = self.repository.get(application_id)
        if application is None:
            raise AppError("semillero.not_found", "La solicitud no existe.", 404)
        return self._advance(
            application_id,
            payload,
            actor,
            key,
            "ASSIGN_REVIEWER",
            application.current_stage,
            application.current_stage,
            reviewer_id=reviewer.id,
        )

    def validate(
        self, application_id: str, payload: ValidationCommand, actor: User, key: str
    ) -> ApplicationRead:
        if payload.eligible and payload.semester < 4:
            raise AppError(
                "semillero.semester_too_low",
                "La modalidad de trabajo de grado exige cuarto semestre o superior.",
                422,
            )
        return self._advance(
            application_id,
            payload,
            actor,
            key,
            "VALIDATE" if payload.eligible else "RETURN_VALIDATION",
            3,
            4 if payload.eligible else 3,
            comment=payload.comment.strip(),
            semester=payload.semester,
        )

    def submit_plan(
        self, application_id: str, payload: PlanCommand, actor: User, key: str
    ) -> ApplicationRead:
        return self._advance(
            application_id,
            payload,
            actor,
            key,
            "SUBMIT_PLAN",
            4,
            4,
            plan_summary=payload.summary.strip(),
            plan_deliverables=payload.deliverables.strip(),
            planned_hours=payload.planned_hours,
            plan_status="SUBMITTED",
        )

    def decide_plan(
        self, application_id: str, payload: PlanDecisionCommand, actor: User, key: str
    ) -> ApplicationRead:
        return self._advance(
            application_id,
            payload,
            actor,
            key,
            "APPROVE_PLAN" if payload.approved else "RETURN_PLAN",
            4,
            5 if payload.approved else 4,
            comment=payload.comment.strip(),
            plan_status="APPROVED" if payload.approved else "RETURNED",
        )

    def _advance(
        self,
        application_id: str,
        payload: object,
        actor: User,
        key: str,
        action: str,
        expected_stage: int,
        next_stage: int,
        *,
        comment: str = "",
        **updates: object,
    ) -> ApplicationRead:
        application = self.repository.get(application_id, for_update=True)
        if application is None:
            raise AppError("semillero.not_found", "La solicitud no existe.", 404)
        digest = body_hash(payload)
        if action == "SUBMIT_PLAN":
            if actor.role != "Estudiante" or application.student_id != actor.id:
                raise PermissionError(
                    "Solo el estudiante titular puede presentar su plan."
                )
        elif action == "ASSIGN_REVIEWER":
            if actor.role != "Super administrador":
                raise PermissionError(
                    "Solo el superadministrador puede asignar un director."
                )
        elif (
            actor.role != "Director de programa" or application.reviewer_id != actor.id
        ):
            raise PermissionError("Solo el director asignado puede decidir esta etapa.")
        prior = self.repository.get_event(application_id, key)
        if prior:
            if (
                prior.request_hash != digest
                or prior.action != action
                or prior.actor_id != actor.id
            ):
                raise AppError(
                    "semillero.idempotency_conflict",
                    "La clave ya se usó con otros datos.",
                    422,
                )
            return ApplicationRead.model_validate(prior.result_snapshot)
        if application.current_stage != expected_stage:
            raise AppError(
                "semillero.invalid_stage", "La etapa ya no admite esta acción.", 409
            )
        if application.version != payload.expected_version:  # type: ignore[attr-defined]
            raise AppError(
                "semillero.stale_version",
                "La solicitud cambió. Actualiza antes de continuar.",
                409,
            )
        if action == "SUBMIT_PLAN" and application.plan_status == "SUBMITTED":
            raise AppError(
                "semillero.plan_pending", "El plan ya está pendiente de revisión.", 409
            )
        if (
            action in {"APPROVE_PLAN", "RETURN_PLAN"}
            and application.plan_status != "SUBMITTED"
        ):
            raise AppError(
                "semillero.plan_not_submitted",
                "No hay un plan pendiente de revisión.",
                409,
            )
        for field, value in updates.items():
            setattr(application, field, value)
        application.current_stage = next_stage
        application.version += 1
        event = self._event(
            application, actor, action, expected_stage, next_stage, comment, key, digest
        )
        try:
            return self.repository.save(application, event)
        except IntegrityError:
            self.db.rollback()
            prior = self.repository.get_event(application_id, key)
            if prior and prior.request_hash == digest and prior.action == action:
                return ApplicationRead.model_validate(prior.result_snapshot)
            raise AppError(
                "semillero.conflict",
                "La solicitud cambió. Actualiza antes de continuar.",
                409,
            ) from None

    @staticmethod
    def _event(
        application: SemilleroApplication,
        actor: User,
        action: str,
        from_stage: int,
        to_stage: int,
        comment: str,
        key: str,
        digest: str,
    ) -> SemilleroEvent:
        return SemilleroEvent(
            id=str(uuid4()),
            application_id=application.id,
            actor_id=actor.id,
            action=action,
            from_stage=from_stage,
            to_stage=to_stage,
            comment=comment,
            idempotency_key=key,
            request_hash=digest,
        )

    @staticmethod
    def _can_read(application: SemilleroApplication, actor: User) -> None:
        if actor.role == "Super administrador":
            return
        if actor.role == "Director de programa" and application.reviewer_id == actor.id:
            return
        if actor.role != "Estudiante" or application.student_id != actor.id:
            raise PermissionError("No puedes consultar esta solicitud.")

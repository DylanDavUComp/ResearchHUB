from copy import deepcopy
from math import isclose
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.modules.trabajos_grado.models import (
    DegreeWorkAuditEvent,
    DegreeWorkCase,
    DegreeWorkModality,
)
from app.modules.trabajos_grado.repository import DegreeWorkRepository
from app.modules.trabajos_grado.schemas import (
    CaseAssignmentCreate,
    CaseCreate,
    CaseTransitionCreate,
    ModalityCreate,
    ModalityUpdate,
)
from app.modules.usuarios.models import User

ADMIN_ROLES = {"Administrador", "Super administrador"}
MANAGEMENT_ROLES = {"Director de programa", "Administrador", "Super administrador"}


def step(
    code: str,
    name: str,
    step_type: str,
    roles: list[str],
    *,
    decision: bool = False,
) -> dict[str, object]:
    return {
        "code": code,
        "name": name,
        "step_type": step_type,
        "responsible_roles": roles,
        "is_decision": decision,
    }


PROJECT_WORKFLOW = [
    step("SELECTION", "Selección de modalidad", "FORM", ["Estudiante"]),
    step("APPLICATION", "Postulación y documentos", "DOCUMENT", ["Estudiante"]),
    step(
        "DOCUMENT_REVIEW",
        "Validación documental",
        "VALIDATION",
        ["Director de programa"],
    ),
    step(
        "FACULTY_APPROVAL",
        "Aval del comité de Facultad",
        "APPROVAL",
        ["Director de programa"],
        decision=True,
    ),
    step("ASSIGNMENT", "Asignación de tutor", "ASSIGNMENT", ["Director de programa"]),
    step("EXECUTION", "Ejecución y seguimiento", "ACTIVITY", ["Estudiante", "Docente"]),
    step("EVALUATION", "Evaluación y sustentación", "EVALUATION", ["Docente"]),
    step(
        "REGISTRATION",
        "Registro de calificación",
        "REGISTRATION",
        ["Director de programa"],
    ),
    step("CLOSURE", "Cierre del proceso", "CLOSURE", ["Director de programa"]),
]

HOMOLOGATION_WORKFLOW = [
    step("ELIGIBILITY", "Validación de elegibilidad", "VALIDATION", ["Estudiante"]),
    step("APPLICATION", "Postulación y documentos", "DOCUMENT", ["Estudiante"]),
    step(
        "DOCUMENT_REVIEW",
        "Validación documental",
        "VALIDATION",
        ["Director de programa"],
    ),
    step(
        "FACULTY_APPROVAL",
        "Aval del comité de Facultad",
        "APPROVAL",
        ["Director de programa"],
        decision=True,
    ),
    step(
        "GENERAL_APPROVAL",
        "Acta del comité general",
        "APPROVAL",
        ["Director de programa"],
        decision=True,
    ),
    step("AGREEMENT", "Acuerdo pedagógico", "DOCUMENT", ["Estudiante"]),
    step("EXECUTION", "Ejecución y seguimiento", "ACTIVITY", ["Estudiante", "Docente"]),
    step("EVALUATION", "Evaluación final", "EVALUATION", ["Docente"]),
    step(
        "HOMOLOGATION",
        "Homologación y registro",
        "REGISTRATION",
        ["Director de programa"],
    ),
    step("CLOSURE", "Cierre del proceso", "CLOSURE", ["Director de programa"]),
]


def criteria(*items: tuple[str, float]) -> list[dict[str, object]]:
    return [{"name": name, "weight": weight} for name, weight in items]


SEED_MODALITIES = [
    {
        "code": "PROYECTO_INVESTIGACION",
        "name": "Proyecto de investigación",
        "description": "Proyecto aplicado con metodología y diseño de investigación.",
        "is_homologatable": False,
        "status": "ACTIVE",
        "initial_semester": 8,
        "duration_label": "16 semanas",
        "min_participants": 3,
        "max_participants": 4,
        "requirements": [{"name": "Matrícula en último semestre"}],
        "evaluation_criteria": criteria(
            ("Trabajo escrito", 20),
            ("Sustentación", 25),
            ("Tutor", 20),
            ("Evaluador 1", 15),
            ("Evaluador 2", 15),
            ("Autoevaluación", 2.5),
            ("Coevaluación", 2.5),
        ),
        "workflow_steps": PROJECT_WORKFLOW,
    },
    {
        "code": "PROYECTO_EMPRENDIMIENTO",
        "name": "Proyecto de emprendimiento",
        "description": "Emprendimiento en fase productiva y con facturación.",
        "is_homologatable": True,
        "status": "ACTIVE",
        "initial_semester": 7,
        "duration_label": "Mínimo 60 horas",
        "min_participants": 1,
        "max_participants": 4,
        "requirements": [{"name": "Emprendimiento 3 o práctica de emprendimiento"}],
        "evaluation_criteria": criteria(
            ("Trabajo escrito", 20),
            ("Sustentación", 25),
            ("Tutor", 20),
            ("Evaluador 1", 15),
            ("Evaluador 2", 15),
            ("Autoevaluación", 2.5),
            ("Coevaluación", 2.5),
        ),
        "workflow_steps": HOMOLOGATION_WORKFLOW,
    },
    {
        "code": "PROYECTO_CONSULTORIA",
        "name": "Proyecto de consultoría",
        "description": "Solución contratada por una organización externa.",
        "is_homologatable": True,
        "status": "ACTIVE",
        "initial_semester": 7,
        "duration_label": "Mínimo 16 semanas",
        "min_participants": 1,
        "max_participants": 4,
        "requirements": [{"name": "Plan de trabajo y mínimo 60 horas"}],
        "evaluation_criteria": criteria(
            ("Trabajo escrito", 20),
            ("Sustentación", 25),
            ("Tutor", 15),
            ("Evaluador", 15),
            ("Empresa cliente", 20),
            ("Autoevaluación", 2.5),
            ("Coevaluación", 2.5),
        ),
        "workflow_steps": HOMOLOGATION_WORKFLOW,
    },
    {
        "code": "PROYECTO_INTERVENCION_SOCIAL",
        "name": "Proyecto de intervención social",
        "description": "Solución de necesidades o problemas de impacto social.",
        "is_homologatable": True,
        "status": "ACTIVE",
        "initial_semester": 6,
        "duration_label": "Mínimo 60 horas",
        "min_participants": 1,
        "max_participants": 4,
        "requirements": [{"name": "Aprobación de comunidad o entidad beneficiaria"}],
        "evaluation_criteria": criteria(
            ("Trabajo escrito", 20),
            ("Sustentación", 25),
            ("Tutor", 20),
            ("Evaluador 1", 15),
            ("Evaluador 2", 15),
            ("Autoevaluación", 2.5),
            ("Coevaluación", 2.5),
        ),
        "workflow_steps": HOMOLOGATION_WORKFLOW,
    },
    {
        "code": "PROYECTO_SEMILLERO_INVESTIGACION",
        "name": "Proyecto de semillero de investigación",
        "description": "Trabajo individual dentro de un semillero constituido.",
        "is_homologatable": True,
        "status": "ACTIVE",
        "initial_semester": 4,
        "duration_label": "Mínimo 60 horas",
        "min_participants": 1,
        "max_participants": 1,
        "requirements": [{"name": "Ingreso formal a semillero de investigación"}],
        "evaluation_criteria": criteria(
            ("Trabajo escrito", 20),
            ("Sustentación", 17.5),
            ("Tutor", 30),
            ("Evaluador 1", 15),
            ("Evaluador 2", 15),
            ("Autoevaluación", 2.5),
        ),
        "workflow_steps": HOMOLOGATION_WORKFLOW,
    },
    {
        "code": "PASANTIA_INVESTIGACION",
        "name": "Pasantía de investigación",
        "description": "Estancia en un grupo de investigación anfitrión.",
        "is_homologatable": True,
        "status": "ACTIVE",
        "initial_semester": 8,
        "duration_label": "Mínimo 16 semanas",
        "min_participants": 1,
        "max_participants": 1,
        "requirements": [{"name": "Convenio con grupo anfitrión cuando sea externo"}],
        "evaluation_criteria": criteria(
            ("Trabajo escrito", 20),
            ("Sustentación", 17.5),
            ("Tutor", 30),
            ("Evaluador", 15),
            ("Grupo anfitrión", 15),
            ("Autoevaluación", 2.5),
        ),
        "workflow_steps": HOMOLOGATION_WORKFLOW,
    },
    {
        "code": "PROYECTO_APLICADO",
        "name": "Proyecto aplicado",
        "description": "Pendiente de definición normativa completa.",
        "is_homologatable": False,
        "status": "INACTIVE",
        "initial_semester": None,
        "duration_label": "Por definir",
        "min_participants": 1,
        "max_participants": 1,
        "requirements": [],
        "evaluation_criteria": [],
        "workflow_steps": [],
    },
    {
        "code": "CURSO_PROFUNDIZACION",
        "name": "Curso de profundización",
        "description": "Curso de perfeccionamiento profesional fuera del plan.",
        "is_homologatable": True,
        "status": "ACTIVE",
        "initial_semester": 8,
        "duration_label": "Mínimo 80 horas",
        "min_participants": 1,
        "max_participants": 1,
        "requirements": [{"name": "Asistencia superior al 80% y nota superior a 3,5"}],
        "evaluation_criteria": [],
        "workflow_steps": HOMOLOGATION_WORKFLOW,
    },
    {
        "code": "INMERSION_INTERNACIONAL",
        "name": "Inmersión internacional",
        "description": "Movilidad para contrastar prácticas profesionales.",
        "is_homologatable": True,
        "status": "ACTIVE",
        "initial_semester": 8,
        "duration_label": "Mínimo 1 semana",
        "min_participants": 1,
        "max_participants": 1,
        "requirements": [{"name": "Pago de movilidad y actividades preparatorias"}],
        "evaluation_criteria": criteria(
            ("Trabajo escrito", 30), ("Sustentación", 15), ("Informe docente", 55)
        ),
        "workflow_steps": HOMOLOGATION_WORKFLOW,
    },
    {
        "code": "PROGRAMA_COTERMINAL",
        "name": "Programa co-terminal",
        "description": "Primer semestre de especialización como opción de grado.",
        "is_homologatable": True,
        "status": "ACTIVE",
        "initial_semester": 8,
        "duration_label": "1 semestre",
        "min_participants": 1,
        "max_participants": 1,
        "requirements": [{"name": "70% de créditos y matrícula activa"}],
        "evaluation_criteria": criteria(("Cursos de especialización", 100)),
        "workflow_steps": HOMOLOGATION_WORKFLOW,
    },
]


class DegreeWorkService:
    def __init__(self, db: Session) -> None:
        self.repository = DegreeWorkRepository(db)
        self.db = db

    def ensure_seed_modalities(self) -> None:
        for item in SEED_MODALITIES:
            if self.repository.get_modality_by_code(str(item["code"])):
                continue
            self.db.add(DegreeWorkModality(id=str(uuid4()), **deepcopy(item)))
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()

    def list_modalities(
        self, include_inactive: bool = False
    ) -> list[DegreeWorkModality]:
        self.ensure_seed_modalities()
        return self.repository.list_modalities(include_inactive)

    def create_modality(
        self, payload: ModalityCreate, actor: User
    ) -> DegreeWorkModality:
        self._require_role(actor, ADMIN_ROLES)
        if self.repository.get_modality_by_code(payload.code):
            raise AppError(
                "degree_work.modality_code_exists",
                "Ya existe una modalidad con este código.",
                409,
            )
        modality = DegreeWorkModality(
            id=str(uuid4()),
            status="DRAFT",
            version=1,
            **payload.model_dump(mode="json"),
        )
        return self.repository.add_modality(modality)

    def update_modality(
        self, modality_id: str, payload: ModalityUpdate, actor: User
    ) -> DegreeWorkModality:
        self._require_role(actor, ADMIN_ROLES)
        modality = self._get_modality(modality_id)
        if modality.status != "DRAFT":
            raise AppError(
                "degree_work.published_modality_immutable",
                "Una modalidad publicada o retirada no se puede editar.",
                409,
            )
        for field, value in payload.model_dump(mode="json").items():
            setattr(modality, field, value)
        modality.version += 1
        return self.repository.save_modality(modality)

    def delete_modality(self, modality_id: str, actor: User) -> None:
        self._require_role(actor, ADMIN_ROLES)
        modality = self._get_modality(modality_id)
        if modality.status != "DRAFT" or self.repository.count_cases_for_modality(
            modality_id
        ):
            raise AppError(
                "degree_work.modality_cannot_delete",
                "Solo se eliminan borradores que nunca han sido utilizados.",
                409,
            )
        self.repository.delete_modality(modality)

    def publish_modality(self, modality_id: str, actor: User) -> DegreeWorkModality:
        self._require_role(actor, {"Super administrador"})
        modality = self._get_modality(modality_id)
        self._validate_for_publication(modality)
        modality.status = "ACTIVE"
        return self.repository.save_modality(modality)

    def retire_modality(self, modality_id: str, actor: User) -> DegreeWorkModality:
        self._require_role(actor, {"Super administrador"})
        modality = self._get_modality(modality_id)
        if modality.status != "ACTIVE":
            raise AppError(
                "degree_work.modality_not_active",
                "Solo una modalidad activa puede retirarse.",
                409,
            )
        modality.status = "RETIRED"
        return self.repository.save_modality(modality)

    def create_case(self, payload: CaseCreate, actor: User) -> DegreeWorkCase:
        self._require_role(actor, {"Estudiante", "Super administrador"})
        self.ensure_seed_modalities()
        modality = self.repository.get_modality_by_code(payload.modality_code)
        if modality is None or modality.status != "ACTIVE":
            raise AppError(
                "degree_work.modality_unavailable",
                "La modalidad no está disponible para nuevas solicitudes.",
                404,
            )
        case = DegreeWorkCase(
            id=str(uuid4()),
            student_id=actor.id,
            modality_id=modality.id,
            modality_code=modality.code,
            modality_name=modality.name,
            modality_version=modality.version,
            title=payload.title.strip(),
            program=payload.program.strip(),
            status="DRAFT",
            current_step_index=0,
            workflow_snapshot=deepcopy(modality.workflow_steps),
        )
        return self.repository.add_case(case)

    def list_cases(self, actor: User) -> list[DegreeWorkCase]:
        if actor.role == "Estudiante":
            return self.repository.list_cases_for_student(actor.id)
        if actor.role == "Docente":
            return self.repository.list_cases_for_teacher(actor.id)
        if actor.role in MANAGEMENT_ROLES:
            return self.repository.list_cases()
        raise PermissionError("El rol no tiene acceso a casos de trabajo de grado.")

    def get_case(self, case_id: str, actor: User) -> DegreeWorkCase:
        case = self._get_case(case_id)
        if actor.role == "Estudiante" and case.student_id != actor.id:
            raise PermissionError("Solo puedes consultar tus propios casos.")
        if actor.role == "Docente" and case.assigned_teacher_id != actor.id:
            raise PermissionError("El caso no está asignado a este docente.")
        if actor.role not in {
            "Estudiante",
            "Docente",
            "Director de programa",
            "Administrador",
            "Super administrador",
        }:
            raise PermissionError("El rol no tiene acceso al caso.")
        return case

    def transition_case(
        self,
        case_id: str,
        payload: CaseTransitionCreate,
        actor: User,
    ) -> DegreeWorkCase:
        case = self.get_case(case_id, actor)
        current_step = case.current_step
        if current_step is None or case.status in {"CLOSED", "REJECTED", "CANCELLED"}:
            raise AppError(
                "degree_work.case_terminal",
                "El caso no admite nuevas transiciones.",
                409,
            )
        roles = current_step.get("responsible_roles", [])
        if actor.role != "Super administrador" and actor.role not in roles:
            raise PermissionError(
                "Tu usuario no tiene el rol responsable de este paso."
            )

        from_status = case.status
        if payload.action == "COMPLETE":
            case.current_step_index += 1
            case.status = (
                "CLOSED"
                if case.current_step_index >= len(case.workflow_snapshot)
                else "IN_PROGRESS"
            )
        elif payload.action == "RETURN":
            case.status = "REQUIRES_CHANGES"
        else:
            case.status = "REJECTED"

        event = DegreeWorkAuditEvent(
            id=str(uuid4()),
            case_id=case.id,
            actor_id=actor.id,
            actor_role=actor.role,
            action=payload.action,
            step_code=str(current_step["code"]),
            from_status=from_status,
            to_status=case.status,
            comment=payload.comment.strip(),
        )
        return self.repository.save_case(case, event)

    def assign_teacher(
        self,
        case_id: str,
        payload: CaseAssignmentCreate,
        actor: User,
    ) -> DegreeWorkCase:
        self._require_role(actor, {"Director de programa", "Super administrador"})
        case = self._get_case(case_id)
        teacher = self.db.get(User, payload.teacher_id)
        if teacher is None or teacher.role != "Docente" or teacher.status != "Activo":
            raise AppError(
                "degree_work.invalid_teacher",
                "El usuario seleccionado no es un docente activo.",
                422,
            )
        case.assigned_teacher_id = teacher.id
        current_step = case.current_step or {"code": "CLOSED"}
        event = DegreeWorkAuditEvent(
            id=str(uuid4()),
            case_id=case.id,
            actor_id=actor.id,
            actor_role=actor.role,
            action="ASSIGN",
            step_code=str(current_step["code"]),
            from_status=case.status,
            to_status=case.status,
            comment=f"Docente asignado: {teacher.name}",
        )
        return self.repository.save_case(case, event)

    def _validate_for_publication(self, modality: DegreeWorkModality) -> None:
        if len(modality.workflow_steps) < 2:
            raise ValueError("La modalidad requiere al menos dos pasos.")
        if any(not item.get("responsible_roles") for item in modality.workflow_steps):
            raise ValueError("Todos los pasos requieren al menos un rol responsable.")
        if modality.evaluation_criteria:
            total = sum(float(item["weight"]) for item in modality.evaluation_criteria)
            if not isclose(total, 100.0, abs_tol=0.01):
                raise ValueError("La rúbrica debe sumar 100%.")

    def _get_modality(self, modality_id: str) -> DegreeWorkModality:
        modality = self.repository.get_modality(modality_id)
        if modality is None:
            raise AppError(
                "degree_work.modality_not_found", "La modalidad no existe.", 404
            )
        return modality

    def _get_case(self, case_id: str) -> DegreeWorkCase:
        case = self.repository.get_case(case_id)
        if case is None:
            raise AppError("degree_work.case_not_found", "El caso no existe.", 404)
        return case

    @staticmethod
    def _require_role(actor: User, roles: set[str]) -> None:
        if actor.role not in roles:
            raise PermissionError("Tu rol no permite realizar esta operación.")

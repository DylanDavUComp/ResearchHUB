from app.core.database import Base
from app.modules.trabajos_grado.models import DegreeWorkCase
from app.modules.trabajos_grado.schemas import (
    CaseAssignmentCreate,
    CaseCreate,
    CaseTransitionCreate,
    ModalityCreate,
)
from app.modules.trabajos_grado.services import DegreeWorkService
from app.modules.usuarios.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def make_user(role: str, user_id: str = "actor-1") -> User:
    return User(
        id=user_id,
        name=role,
        email=f"{user_id}@ucompensar.edu.co",
        role=role,
        status="Activo",
        password_hash="not-used",
        permissions=[],
    )


def test_seed_contains_all_policy_modalities_and_keeps_applied_project_inactive(
) -> None:
    with make_session() as db:
        service = DegreeWorkService(db)

        modalities = service.list_modalities(include_inactive=True)

        assert len(modalities) == 10
        applied = next(item for item in modalities if item.code == "PROYECTO_APLICADO")
        assert applied.status == "INACTIVE"
        assert applied.workflow_steps == []


def test_draft_modality_requires_a_complete_workflow_before_publication() -> None:
    with make_session() as db:
        service = DegreeWorkService(db)
        admin = make_user("Administrador")
        superadmin = make_user("Super administrador", "super-1")
        modality = service.create_modality(
            ModalityCreate(
                code="MODALIDAD_PRUEBA",
                name="Modalidad de prueba",
                description="Valida el ciclo de publicación.",
                is_homologatable=False,
                min_participants=1,
                max_participants=2,
                requirements=[],
                evaluation_criteria=[],
                workflow_steps=[],
            ),
            admin,
        )

        try:
            service.publish_modality(modality.id, superadmin)
        except ValueError as exc:
            assert str(exc) == "La modalidad requiere al menos dos pasos."
        else:
            raise AssertionError("La modalidad sin flujo no se debe publicar")


def test_case_uses_modality_workflow_and_only_responsible_role_can_advance() -> None:
    with make_session() as db:
        service = DegreeWorkService(db)
        student = make_user("Estudiante", "student-1")
        teacher = make_user("Docente", "teacher-1")
        case = service.create_case(
            CaseCreate(
                modality_code="PROYECTO_INVESTIGACION",
                title="Analítica para permanencia estudiantil",
                program="Ingeniería de software",
            ),
            student,
        )

        assert case.status == "DRAFT"
        assert case.current_step["responsible_roles"] == ["Estudiante"]
        case.assigned_teacher_id = teacher.id
        db.commit()

        try:
            service.transition_case(
                case.id,
                CaseTransitionCreate(action="COMPLETE", comment="Revisado"),
                teacher,
            )
        except PermissionError as exc:
            assert "rol responsable" in str(exc)
        else:
            raise AssertionError("Un docente no debe ejecutar el paso del estudiante")

        advanced = service.transition_case(
            case.id,
            CaseTransitionCreate(action="COMPLETE", comment="Modalidad seleccionada"),
            student,
        )

        assert advanced.current_step_index == 1
        assert advanced.status == "IN_PROGRESS"
        assert db.query(DegreeWorkCase).count() == 1
        assert len(advanced.history) == 1


def test_student_only_lists_own_cases_while_director_lists_program_cases() -> None:
    with make_session() as db:
        service = DegreeWorkService(db)
        first_student = make_user("Estudiante", "student-1")
        second_student = make_user("Estudiante", "student-2")
        director = make_user("Director de programa", "director-1")
        for student, title in (
            (first_student, "Caso uno"),
            (second_student, "Caso dos"),
        ):
            service.create_case(
                CaseCreate(
                    modality_code="PROYECTO_INVESTIGACION",
                    title=title,
                    program="Ingeniería de software",
                ),
                student,
            )

        assert len(service.list_cases(first_student)) == 1
        assert len(service.list_cases(director)) == 2


def test_director_assigns_teacher_and_case_appears_in_teacher_inbox() -> None:
    with make_session() as db:
        service = DegreeWorkService(db)
        student = make_user("Estudiante", "student-1")
        teacher = make_user("Docente", "teacher-1")
        director = make_user("Director de programa", "director-1")
        db.add_all([student, teacher, director])
        db.commit()
        case = service.create_case(
            CaseCreate(
                modality_code="PROYECTO_INVESTIGACION",
                title="Caso con docente asignado",
                program="Ingeniería de software",
            ),
            student,
        )

        assigned = service.assign_teacher(
            case.id,
            CaseAssignmentCreate(teacher_id=teacher.id),
            director,
        )

        assert assigned.assigned_teacher_id == teacher.id
        assert service.list_cases(teacher)[0].id == case.id
        assert assigned.history[-1].action == "ASSIGN"

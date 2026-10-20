from app.modules.research_os.schemas import WorkspaceRead, WorkspaceSection
from app.modules.usuarios.models import User
from app.modules.usuarios.services.user_service import to_read_model

# Secciones aprobadas en SPEC-ROS-001. Ninguna tiene aun capacidad operativa, por lo
# que se publican como no disponibles en lugar de simular funcionalidad.
SECTIONS: tuple[WorkspaceSection, ...] = (
    WorkspaceSection(
        code="applied_projects",
        name="Proyectos aplicados",
        description="Proyectos de investigación aplicada, alianzas y seguimiento.",
        available=False,
    ),
    WorkspaceSection(
        code="capabilities",
        name="Capacidades",
        description="Laboratorios, equipos, servicios y experticia institucional.",
        available=False,
    ),
    WorkspaceSection(
        code="results",
        name="Resultados de investigación",
        description="Productos, prototipos y resultados verificables.",
        available=False,
    ),
    WorkspaceSection(
        code="transfer",
        name="Transferencia",
        description="Licenciamiento, consultoría y transferencia al entorno.",
        available=False,
    ),
)


class ResearchOsService:
    def workspace(self, user: User) -> WorkspaceRead:
        return WorkspaceRead(user=to_read_model(user), sections=list(SECTIONS))

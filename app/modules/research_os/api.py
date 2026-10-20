from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import require_application
from app.modules.research_os.schemas import WorkspaceRead
from app.modules.research_os.services import ResearchOsService
from app.modules.usuarios.models import User

router = APIRouter(prefix="/research-os", tags=["researchos"])

research_os_user = Annotated[User, Depends(require_application("research_os"))]


@router.get(
    "/workspace",
    response_model=WorkspaceRead,
    summary="Espacio de trabajo de ResearchOS del usuario autenticado",
)
def read_workspace(current_user: research_os_user) -> WorkspaceRead:
    return ResearchOsService().workspace(current_user)

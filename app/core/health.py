from fastapi import APIRouter, Response, status

from app.core.config import settings
from app.core.database import database_is_ready

router = APIRouter(prefix="/health", tags=["health"])


def health_payload(state: str = "ok") -> dict[str, str]:
    return {
        "status": state,
        "service": settings.service_name,
        "version": settings.app_version,
    }


@router.get("/live", summary="Liveness check")
def live() -> dict[str, str]:
    return health_payload()


@router.get("/ready", summary="Readiness check")
def ready(response: Response) -> dict[str, str]:
    if not database_is_ready():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return health_payload("not_ready")
    return health_payload()

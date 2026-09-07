from fastapi import APIRouter

from app.core.config import settings
from app.core.health import router as health_router
from app.modules.admin.api.routes import router as admin_router
from app.modules.homologaciones.api.routes import router as homologaciones_router
from app.modules.usuarios.api.routes import router as usuarios_router

api_router = APIRouter()
api_router.include_router(health_router)

versioned_router = APIRouter(prefix=settings.api_v1_prefix)


@versioned_router.get("/meta", summary="Application metadata")
def read_meta() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "service": settings.service_name,
        "version": settings.app_version,
    }


versioned_router.include_router(homologaciones_router)
versioned_router.include_router(usuarios_router)
versioned_router.include_router(admin_router)
api_router.include_router(versioned_router)

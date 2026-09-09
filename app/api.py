from fastapi import APIRouter

from app.core.config import settings
from app.core.health import router as health_router
from app.modules.admin.api.routes import router as admin_router
from app.modules.homologaciones.api.routes import router as homologaciones_router
from app.modules.trabajos_grado.api import router as trabajos_grado_router
from app.modules.usuarios.api.routes import router as usuarios_router

api_router = APIRouter()
api_router.include_router(health_router)

versioned_router = APIRouter(prefix=settings.api_v1_prefix)


@versioned_router.get("/meta", summary="Application metadata")
def read_meta() -> dict[str, object]:
    return {
        "name": settings.app_name,
        "service": settings.service_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "features": {
            "self_registration": settings.self_registration_enabled,
        },
        "applications": {
            "research_hub_u": {
                "available": True,
                "url": "/",
            },
            "research_os": {
                "available": bool(settings.research_os_url),
                "url": settings.research_os_url,
            },
            "cris": {
                "available": bool(settings.cris_url),
                "url": settings.cris_url,
            },
            "crai": {
                "available": bool(settings.crai_url),
                "url": settings.crai_url,
            },
            "services_marketplace": {
                "available": bool(settings.services_marketplace_url),
                "url": settings.services_marketplace_url,
            },
        },
        "links": {
            "research_blog": {
                "available": bool(settings.research_blog_url),
                "url": settings.research_blog_url,
            },
        },
    }


versioned_router.include_router(homologaciones_router)
versioned_router.include_router(trabajos_grado_router)
versioned_router.include_router(usuarios_router)
versioned_router.include_router(admin_router)
api_router.include_router(versioned_router)

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.database import list_database_tables
from app.core.security import require_superadmin
from app.modules.usuarios.models import User

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get(
    "/databases",
    summary="Read-only project database catalog",
)
def read_databases(
    _: User = Depends(require_superadmin),
) -> dict[str, object]:

    return {
        "mode": "read_only",
        "databases": [
            {
                "name": settings.postgres_db,
                "engine": "PostgreSQL",
                "host": settings.postgres_host,
                "port": settings.postgres_port,
                "docker_volume": "postgres_data",
                "internal_directory": "/var/lib/postgresql/data",
                "tables": list_database_tables(),
            }
        ],
    }

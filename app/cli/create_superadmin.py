import logging
from collections.abc import Callable
from getpass import getpass

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.core.database import get_session_factory
from app.core.logging import configure_logging
from app.modules.usuarios.services.user_service import bootstrap_superadmin

MIN_PASSWORD_LENGTH = 16


def create_superadmin(
    db: Session,
    config: Settings,
    read_text: Callable[[str], str] = input,
    read_secret: Callable[[str], str] = getpass,
) -> str:
    name = read_text("Nombre completo: ").strip()
    email = read_text("Correo institucional: ").strip().lower()
    password = read_secret(f"Clave (minimo {MIN_PASSWORD_LENGTH} caracteres): ")
    if not name or not email:
        return "invalid"
    if len(password) < MIN_PASSWORD_LENGTH:
        return "weak_password"
    if read_secret("Repite la clave: ") != password:
        return "password_mismatch"
    interactive_config = config.model_copy(
        update={
            "bootstrap_superadmin_enabled": True,
            "bootstrap_superadmin_name": name,
            "bootstrap_superadmin_email": email,
            "bootstrap_superadmin_password": password,
        }
    )
    return bootstrap_superadmin(db, interactive_config)


def main() -> int:
    configure_logging(settings.log_level)
    logger = logging.getLogger("researchhub.create_superadmin")
    with get_session_factory()() as db:
        result = create_superadmin(db, settings)
    logger.info("superadmin_create_%s", result)
    print(f"Resultado: {result}")
    return 0 if result in {"created", "exists"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

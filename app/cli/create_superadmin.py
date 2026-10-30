"""Crea un superadministrador pidiendo los datos en una terminal interactiva.

Las credenciales no pasan por archivos, variables de entorno ni argumentos de linea
de comandos: se leen del teclado y solo se persiste su hash en PostgreSQL.

    docker compose exec api python -m app.cli.create_superadmin
"""

import getpass
import logging
import sys
from collections.abc import Callable

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_session_factory
from app.core.logging import configure_logging
from app.modules.usuarios.services.user_service import create_superadmin

MIN_PASSWORD_LENGTH = 16
MAX_PASSWORD_LENGTH = 128

logger = logging.getLogger("researchhub.superadmin")


def collect_credentials(
    read_line: Callable[[str], str],
    read_secret: Callable[[str], str],
    write: Callable[[str], None],
) -> tuple[str, str, str] | None:
    name = read_line("Nombre completo: ").strip()
    email = read_line("Correo: ").strip().lower()
    password = read_secret(f"Contraseña ({MIN_PASSWORD_LENGTH}+ caracteres): ")
    confirmation = read_secret("Confirma la contraseña: ")

    if not name or len(name) > 160:
        write("El nombre es obligatorio y tiene máximo 160 caracteres.")
        return None
    if "@" not in email or len(email) > 255:
        write("El correo no es válido.")
        return None
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        write(
            f"La contraseña debe tener entre {MIN_PASSWORD_LENGTH} y "
            f"{MAX_PASSWORD_LENGTH} caracteres."
        )
        return None
    if password != confirmation:
        write("Las contraseñas no coinciden.")
        return None
    return name, email, password


def run(
    session_factory: Callable[[], Session],
    read_line: Callable[[str], str],
    read_secret: Callable[[str], str],
    write: Callable[[str], None],
    is_interactive: bool,
) -> int:
    if not is_interactive:
        write(
            "Ejecuta este comando en una terminal interactiva; no acepta "
            "credenciales desde archivos ni tuberias."
        )
        return 2

    credentials = collect_credentials(read_line, read_secret, write)
    if credentials is None:
        return 1

    name, email, password = credentials
    try:
        with session_factory() as db:
            result = create_superadmin(db, name, email, password)
    except ValidationError:
        write("Los datos no cumplen las reglas de la cuenta.")
        return 1

    if result == "exists":
        write("Ya existe una cuenta con ese correo; no se modificó.")
        logger.info("superadmin_exists")
        return 1

    write("Superadministrador creado en PostgreSQL.")
    logger.info("superadmin_created")
    return 0


def main() -> None:
    configure_logging(settings.log_level)
    sys.exit(
        run(
            session_factory=get_session_factory(),
            read_line=input,
            read_secret=getpass.getpass,
            write=print,
            is_interactive=sys.stdin.isatty(),
        )
    )


if __name__ == "__main__":
    main()

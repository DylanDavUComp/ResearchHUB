"""Deja un comunicado como borrador para que un superadministrador lo apruebe.

El contenido llega como JSON por la entrada estandar y se valida con las mismas
reglas del formulario. Nunca publica: el borrador espera en la consola de
configuracion general hasta que alguien lo apruebe o lo descarte.

    docker compose exec -T api python -m app.cli.create_announcement_draft \
        --author superadmin@ucompensar.edu.co < comunicado.json
"""

import argparse
import json
import logging
import sys
from collections.abc import Callable

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_session_factory
from app.core.logging import configure_logging
from app.modules.comunicados.repository import AnnouncementRepository
from app.modules.comunicados.schemas import AnnouncementCreate
from app.modules.comunicados.services import AnnouncementService
from app.modules.usuarios.models import User

logger = logging.getLogger("researchhub.announcements")


def run(
    session_factory: Callable[[], Session],
    author_email: str,
    raw_content: str,
    write: Callable[[str], None],
) -> int:
    try:
        payload = AnnouncementCreate.model_validate(json.loads(raw_content))
    except json.JSONDecodeError:
        write("El contenido no es un JSON válido.")
        return 1
    except ValidationError as error:
        fields = ", ".join(sorted({str(item["loc"][-1]) for item in error.errors()}))
        write(f"El comunicado no cumple las reglas del formulario: {fields}.")
        return 1

    with session_factory() as db:
        author = db.scalar(
            select(User).where(User.email == author_email.strip().lower())
        )
        if author is None or author.status != "Activo":
            write("No existe una cuenta activa con ese correo.")
            return 1
        if author.role != "Super administrador":
            write("La cuenta autora debe tener el rol Super administrador.")
            return 1
        if AnnouncementRepository(db).exists_with_title(payload.title):
            write("Ya existe un comunicado con ese título; no se creó otro.")
            logger.info("announcement_draft_exists")
            return 1
        draft_id = AnnouncementService(db).create(payload, author).id

    write(f"Borrador creado: «{payload.title}». Apruébalo en /configuracion.")
    logger.info("announcement_draft_created", extra={"announcement_id": draft_id})
    return 0


def main() -> None:
    configure_logging(settings.log_level)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--author", required=True, help="Correo del superadministrador")
    args = parser.parse_args()
    sys.exit(
        run(
            session_factory=get_session_factory(),
            author_email=args.author,
            raw_content=sys.stdin.read(),
            write=print,
        )
    )


if __name__ == "__main__":
    main()

import json

import pytest
from app.cli.create_announcement_draft import run
from app.modules.comunicados.models import Announcement, AnnouncementAuditEvent
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.unit.auth_support import create_user

SUPERADMIN = "super@ucompensar.edu.co"
CONTENT = {
    "category": "CONVOCATORIA",
    "title": "Abierta la Convocatoria Interna 2027 para proyectos I+D+C+i",
    "summary": "La Dirección de Investigación y Transferencia abre la convocatoria.",
    "body": "Primer párrafo.\n\nSegundo párrafo.",
}


@pytest.fixture
def superadmin(session_factory: sessionmaker[Session]) -> str:
    return create_user(session_factory, SUPERADMIN, [], "Super administrador")


def execute(
    session_factory: sessionmaker[Session],
    content: object = CONTENT,
    author: str = SUPERADMIN,
) -> tuple[int, list[str]]:
    output: list[str] = []
    raw = content if isinstance(content, str) else json.dumps(content)
    return run(session_factory, author, raw, output.append), output


def announcements(session_factory: sessionmaker[Session]) -> list[Announcement]:
    with session_factory() as db:
        return list(db.scalars(select(Announcement)))


def test_creates_a_draft_waiting_for_approval(
    session_factory: sessionmaker[Session], superadmin: str
) -> None:
    code, output = execute(session_factory)

    created = announcements(session_factory)
    assert code == 0
    assert len(created) == 1
    assert created[0].status == "DRAFT"
    assert created[0].published_at is None
    assert created[0].author_id == superadmin
    assert created[0].body == CONTENT["body"]
    assert "/configuracion" in output[0]
    with session_factory() as db:
        event = db.scalars(select(AnnouncementAuditEvent)).one()
    assert (event.action, event.actor_id) == ("CREATE", superadmin)


def test_running_twice_does_not_duplicate_the_draft(
    session_factory: sessionmaker[Session], superadmin: str
) -> None:
    execute(session_factory)

    code, output = execute(session_factory)

    assert code == 1
    assert len(announcements(session_factory)) == 1
    assert output == ["Ya existe un comunicado con ese título; no se creó otro."]


def test_author_must_be_superadmin(session_factory: sessionmaker[Session]) -> None:
    create_user(session_factory, "admin@ucompensar.edu.co", [], "Administrador")

    code, output = execute(session_factory, author="admin@ucompensar.edu.co")

    assert code == 1
    assert announcements(session_factory) == []
    assert output == ["La cuenta autora debe tener el rol Super administrador."]


def test_unknown_author_is_rejected(session_factory: sessionmaker[Session]) -> None:
    code, output = execute(session_factory, author="nadie@ucompensar.edu.co")

    assert code == 1
    assert output == ["No existe una cuenta activa con ese correo."]


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("{no es json", "El contenido no es un JSON válido."),
        (
            {**CONTENT, "link_url": "http://inseguro.example.com"},
            "El comunicado no cumple las reglas del formulario: link_url.",
        ),
    ],
)
def test_invalid_content_creates_nothing(
    session_factory: sessionmaker[Session],
    superadmin: str,
    content: object,
    message: str,
) -> None:
    code, output = execute(session_factory, content=content)

    assert code == 1
    assert output == [message]
    assert announcements(session_factory) == []

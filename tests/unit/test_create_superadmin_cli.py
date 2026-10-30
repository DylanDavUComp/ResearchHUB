from collections.abc import Callable

from app.cli.create_superadmin import run
from app.modules.usuarios.models import User
from app.modules.usuarios.services.user_service import verify_password
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

PASSWORD = "Clave-superadmin-segura-2026"


def answers(*values: str) -> Callable[[str], str]:
    queue = list(values)
    return lambda _prompt: queue.pop(0)


def execute(
    session_factory: sessionmaker[Session],
    lines: tuple[str, ...] = ("Super administrador", "Superadmin@Researchhub-u.edu.co"),
    secrets: tuple[str, ...] = (PASSWORD, PASSWORD),
    is_interactive: bool = True,
) -> tuple[int, list[str]]:
    output: list[str] = []
    code = run(
        session_factory=session_factory,
        read_line=answers(*lines),
        read_secret=answers(*secrets),
        write=output.append,
        is_interactive=is_interactive,
    )
    return code, output


def users(session_factory: sessionmaker[Session]) -> list[User]:
    with session_factory() as db:
        return list(db.scalars(select(User)))


def test_creates_superadmin_in_the_database(
    session_factory: sessionmaker[Session],
) -> None:
    code, output = execute(session_factory)

    created = users(session_factory)
    assert code == 0
    assert output == ["Superadministrador creado en PostgreSQL."]
    assert len(created) == 1
    assert created[0].email == "superadmin@researchhub-u.edu.co"
    assert created[0].role == "Super administrador"
    assert verify_password(PASSWORD, created[0].password_hash)


def test_never_prints_the_password(session_factory: sessionmaker[Session]) -> None:
    _, output = execute(session_factory)

    assert all(PASSWORD not in line for line in output)


def test_refuses_non_interactive_execution(
    session_factory: sessionmaker[Session],
) -> None:
    code, _ = execute(session_factory, is_interactive=False)

    assert code == 2
    assert users(session_factory) == []


def test_rejects_short_password(session_factory: sessionmaker[Session]) -> None:
    code, output = execute(session_factory, secrets=("corta-123", "corta-123"))

    assert code == 1
    assert "entre 16 y 128" in output[0]
    assert users(session_factory) == []


def test_rejects_mismatched_confirmation(
    session_factory: sessionmaker[Session],
) -> None:
    code, output = execute(session_factory, secrets=(PASSWORD, PASSWORD + "x"))

    assert code == 1
    assert output == ["Las contraseñas no coinciden."]
    assert users(session_factory) == []


def test_rejects_invalid_email(session_factory: sessionmaker[Session]) -> None:
    code, _ = execute(session_factory, lines=("Super administrador", "sin-arroba"))

    assert code == 1
    assert users(session_factory) == []


def test_does_not_touch_an_existing_account(
    session_factory: sessionmaker[Session],
) -> None:
    execute(session_factory)

    code, output = execute(
        session_factory,
        secrets=("Otra-clave-muy-segura-2026", "Otra-clave-muy-segura-2026"),
    )

    stored = users(session_factory)
    assert code == 1
    assert output == ["Ya existe una cuenta con ese correo; no se modificó."]
    assert len(stored) == 1
    assert verify_password(PASSWORD, stored[0].password_hash)

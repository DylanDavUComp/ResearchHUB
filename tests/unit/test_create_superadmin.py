from collections.abc import Callable, Iterator

from app.cli.create_superadmin import create_superadmin
from app.core.config import Settings
from app.core.database import Base
from app.modules.usuarios.models import User
from app.modules.usuarios.services.user_service import ALL_PERMISSIONS, verify_password
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

PASSWORD = "SuperAdminPassword-2026"


def local_settings() -> Settings:
    return Settings(
        secret_key="a-secure-local-secret-with-at-least-32-characters",
        _env_file=None,
    )


def database_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def answers(*values: str) -> Callable[[str], str]:
    pending: Iterator[str] = iter(values)
    return lambda _prompt: next(pending)


def test_creates_superadmin_with_hashed_password() -> None:
    with database_session() as db:
        result = create_superadmin(
            db,
            local_settings(),
            read_text=answers("Admin Inicial", " Admin@UCompensar.edu.co "),
            read_secret=answers(PASSWORD, PASSWORD),
        )
        user = db.scalar(select(User))

    assert result == "created"
    assert user is not None
    assert user.email == "admin@ucompensar.edu.co"
    assert user.role == "Super administrador"
    assert user.permissions == ALL_PERMISSIONS
    assert user.password_hash != PASSWORD
    assert verify_password(PASSWORD, user.password_hash)


def test_existing_email_is_not_modified() -> None:
    with database_session() as db:
        for password in (PASSWORD, "OtherPassword-2026-long"):
            result = create_superadmin(
                db,
                local_settings(),
                read_text=answers("Admin", "admin@ucompensar.edu.co"),
                read_secret=answers(password, password),
            )
        user = db.scalar(select(User))

    assert result == "exists"
    assert user is not None
    assert verify_password(PASSWORD, user.password_hash)


def test_rejects_short_or_mismatched_password_without_creating() -> None:
    with database_session() as db:
        weak = create_superadmin(
            db,
            local_settings(),
            read_text=answers("Admin", "admin@ucompensar.edu.co"),
            read_secret=answers("short-password"),
        )
        mismatch = create_superadmin(
            db,
            local_settings(),
            read_text=answers("Admin", "admin@ucompensar.edu.co"),
            read_secret=answers(PASSWORD, PASSWORD + "x"),
        )
        empty = create_superadmin(
            db,
            local_settings(),
            read_text=answers("", "admin@ucompensar.edu.co"),
            read_secret=answers(PASSWORD, PASSWORD),
        )
        users = db.scalars(select(User)).all()

    assert (weak, mismatch, empty) == ("weak_password", "password_mismatch", "invalid")
    assert users == []

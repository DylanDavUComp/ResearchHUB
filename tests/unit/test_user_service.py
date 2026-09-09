import hashlib

from app.core.config import Settings
from app.core.database import Base
from app.core.exceptions import AppError
from app.modules.usuarios.models import User
from app.modules.usuarios.schemas.user import UserCreate, UserLogin, UserRegister
from app.modules.usuarios.services.user_service import (
    ALL_PERMISSIONS,
    UserService,
    bootstrap_superadmin,
    hash_password,
    verify_password,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def local_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "secret_key": "a-secure-local-secret-with-at-least-32-characters",
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)


def database_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_password_hash_uses_scrypt_and_verifies() -> None:
    password_hash = hash_password("StrongPassword-2026")

    assert password_hash.startswith("scrypt$")
    assert verify_password("StrongPassword-2026", password_hash)
    assert not verify_password("incorrect", password_hash)


def test_legacy_pbkdf2_password_is_upgraded_after_login() -> None:
    password = "ExistingPassword-2026"
    salt = b"0123456789abcdef"
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    legacy_hash = f"pbkdf2_sha256${salt.hex()}${digest.hex()}"

    with database_session() as db:
        db.add(
            User(
                id="legacy-user",
                name="Usuario existente",
                email="legacy@ucompensar.edu.co",
                role="Estudiante",
                status="Activo",
                password_hash=legacy_hash,
                permissions=[],
            )
        )
        db.commit()
        service = UserService(db, local_settings())

        service.authenticate(
            UserLogin(
                email="legacy@ucompensar.edu.co",
                password=password,
            )
        )

        db.expire_all()
        user = db.get(User, "legacy-user")
        assert user is not None
        assert user.password_hash.startswith("scrypt$")


def test_self_registration_is_disabled_by_default() -> None:
    with database_session() as db:
        service = UserService(db, local_settings())

        try:
            service.register(
                UserRegister(
                    name="Estudiante",
                    email="estudiante@ucompensar.edu.co",
                    password="StrongPassword-2026",
                )
            )
        except AppError as exc:
            assert exc.code == "users.self_registration_disabled"
            assert exc.status_code == 403
        else:
            raise AssertionError("El registro publico debio estar deshabilitado")


def test_bootstrap_creates_superadmin_only_when_explicitly_enabled() -> None:
    config = local_settings(
        bootstrap_superadmin_enabled=True,
        bootstrap_superadmin_name="Operador inicial",
        bootstrap_superadmin_email="operador@ucompensar.edu.co",
        bootstrap_superadmin_password="StrongBootstrapPassword-2026",
    )

    with database_session() as db:
        assert bootstrap_superadmin(db, config) == "created"
        user = db.query(User).one()

        assert user.email == "operador@ucompensar.edu.co"
        assert user.permissions == ALL_PERMISSIONS
        assert verify_password("StrongBootstrapPassword-2026", user.password_hash)


def test_bootstrap_never_resets_an_existing_account() -> None:
    config = local_settings(
        bootstrap_superadmin_enabled=True,
        bootstrap_superadmin_name="Operador reemplazo",
        bootstrap_superadmin_email="operador@ucompensar.edu.co",
        bootstrap_superadmin_password="NewBootstrapPassword-2026",
    )

    with database_session() as db:
        service = UserService(db, config)
        service.create(
            UserCreate(
                name="Operador existente",
                email="operador@ucompensar.edu.co",
                role="Super administrador",
                password="ExistingPassword-2026",
                permissions=[],
            )
        )

        assert bootstrap_superadmin(db, config) == "exists"
        user = db.query(User).one()
        assert user.name == "Operador existente"
        assert verify_password("ExistingPassword-2026", user.password_hash)
        assert not verify_password("NewBootstrapPassword-2026", user.password_hash)

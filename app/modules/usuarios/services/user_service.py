import hashlib
import hmac
import os
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.modules.usuarios.schemas.user import LoginResponse

from app.core.exceptions import AppError
from app.modules.usuarios.models import User
from app.modules.usuarios.repository import UserRepository
from app.core.security import create_access_token
from app.modules.usuarios.schemas.user import (
    LoginResponse,
    UserCreate,
    UserLogin,
    UserRead,
    UserRegister,
    UserUpdate,
)

ALL_PERMISSIONS = [
    "users:create",
    "users:read",
    "users:update",
    "users:delete",
    "settings:manage",
]

SEED_USERS = [
    UserCreate(
        name="Super Administrador",
        email="superadmin@researchhub-u.edu.co",
        role="Super administrador",
        status="Activo",
        password="ResearchHubU2026!",
        permissions=ALL_PERMISSIONS,
    ),
    UserCreate(
        name="Maria Gonzalez",
        email="maria.gonzalez@ucompensar.edu.co",
        role="Estudiante",
        status="Activo",
        password="Estudiante2026!",
        permissions=[],
    ),
    UserCreate(
        name="Carlos Ramirez",
        email="carlos.ramirez@ucompensar.edu.co",
        role="Coordinador de programa",
        status="Activo",
        password="Coordinador2026!",
        permissions=["users:read", "users:update"],
    ),
]


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = password_hash.split("$", 2)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    expected = bytes.fromhex(digest_hex)
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt_hex),
        120_000,
    )
    return hmac.compare_digest(actual, expected)


def to_read_model(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        status=user.status,
        permissions=list(user.permissions or []),
    )


class UserService:
    def __init__(self, db: Session) -> None:
        self.repository = UserRepository(db)

    def ensure_seed_users(self) -> None:
        for payload in SEED_USERS:
            existing = self.repository.get_by_email(payload.email.strip().lower())
            if existing is None:
                self.create(payload)
                continue

            if payload.role != "Super administrador":
                continue

            existing.name = payload.name
            existing.role = payload.role
            existing.status = "Activo"
            existing.permissions = ALL_PERMISSIONS
            if not verify_password(payload.password, existing.password_hash):
                existing.password_hash = hash_password(payload.password)
            self.repository.update(existing)

    def list(self) -> list[UserRead]:
        self.ensure_seed_users()
        return [to_read_model(user) for user in self.repository.list()]

    def create(self, payload: UserCreate) -> UserRead:
        email = payload.email.strip().lower()
        if self.repository.get_by_email(email):
            raise AppError(
                code="users.email_taken",
                message="Ya existe un usuario con ese correo institucional.",
                status_code=409,
            )

        permissions = (
            ALL_PERMISSIONS
            if payload.role == "Super administrador"
            else payload.permissions
        )
        user = User(
            id=str(uuid4()),
            name=payload.name.strip(),
            email=email,
            role=payload.role,
            status=payload.status,
            password_hash=hash_password(payload.password),
            permissions=permissions,
        )
        return to_read_model(self.repository.add(user))
    
    def register(self, payload: UserRegister) -> UserRead:
        email = payload.email.strip().lower()

        if not email.endswith("@ucompensar.edu.co"):
            raise AppError(
                code="users.invalid_institutional_email",
                message=(
                    "Solo se permiten correos institucionales "
                    "@ucompensar.edu.co."
                ),
                status_code=400,
            )

        if self.repository.get_by_email(email):
            raise AppError(
                code="users.email_taken",
                message="Ya existe un usuario con ese correo institucional.",
                status_code=409,
            )

        user = User(
            id=str(uuid4()),
            name=payload.name.strip(),
            email=email,
            role="Estudiante",
            status="Activo",
            password_hash=hash_password(payload.password),
            permissions=[],
        )

        return to_read_model(self.repository.add(user))

    def update(self, user_id: str, payload: UserUpdate) -> UserRead:
        user = self.repository.get(user_id)
        if user is None:
            raise AppError(
                code="users.not_found",
                message="El usuario no existe.",
                status_code=404,
            )

        email = payload.email.strip().lower()
        existing = self.repository.get_by_email(email)
        if existing and existing.id != user_id:
            raise AppError(
                code="users.email_taken",
                message="Ya existe un usuario con ese correo institucional.",
                status_code=409,
            )

        user.name = payload.name.strip()
        user.email = email
        user.role = payload.role
        user.status = payload.status
        user.permissions = (
            ALL_PERMISSIONS
            if payload.role == "Super administrador"
            else payload.permissions
        )
        if payload.password:
            user.password_hash = hash_password(payload.password)

        return to_read_model(self.repository.update(user))

    def delete(self, user_id: str) -> None:
        user = self.repository.get(user_id)
        if user is None:
            raise AppError(
                code="users.not_found",
                message="El usuario no existe.",
                status_code=404,
            )

        if user.role == "Super administrador":
            raise AppError(
                code="users.superadmin_protected",
                message="No se puede eliminar un superadministrador.",
                status_code=400,
            )

        self.repository.delete(user)

    def authenticate(self, payload: UserLogin) -> LoginResponse:
        self.ensure_seed_users()

        user = self.repository.get_by_email(payload.email.strip().lower())

        if (
            user is None
            or user.status != "Activo"
            or not verify_password(
                payload.password,
                user.password_hash,
            )
        ):
            raise AppError(
                code="users.invalid_credentials",
                message="Credenciales invalidas o usuario inactivo.",
                status_code=401,
            )

        token = create_access_token(user.id)

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user=to_read_model(user),
        )

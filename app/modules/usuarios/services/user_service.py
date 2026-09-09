import hashlib
import hmac
import os
from typing import Literal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.core.exceptions import AppError
from app.core.security import create_access_token
from app.modules.usuarios.models import User
from app.modules.usuarios.repository import UserRepository
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
    "degree_work:self:create",
    "degree_work:self:read",
    "degree_work:self:submit",
    "degree_work:assigned:read",
    "degree_work:assigned:review",
    "degree_work:assigned:evaluate",
    "degree_work:program:read",
    "degree_work:program:decide",
    "degree_work:program:assign",
    "degree_work:program:report",
    "degree_work:any:read",
    "degree_work:any:support",
    "modalities:read",
    "modalities:create",
    "modalities:update",
    "modalities:delete",
    "modalities:publish",
    "modalities:retire",
    "audit:any:read",
]


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=64,
    )
    return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    parts = password_hash.split("$")
    try:
        if len(parts) == 6 and parts[0] == "scrypt":
            _, n, r, p, salt_hex, digest_hex = parts
            expected = bytes.fromhex(digest_hex)
            actual = hashlib.scrypt(
                password.encode(),
                salt=bytes.fromhex(salt_hex),
                n=int(n),
                r=int(r),
                p=int(p),
                dklen=len(expected),
            )
            return hmac.compare_digest(actual, expected)

        if len(parts) == 3 and parts[0] == "pbkdf2_sha256":
            _, salt_hex, digest_hex = parts
            expected = bytes.fromhex(digest_hex)
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                bytes.fromhex(salt_hex),
                120_000,
            )
            return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False
    return False


def password_needs_rehash(password_hash: str) -> bool:
    return not password_hash.startswith("scrypt$16384$8$1$")


DUMMY_PASSWORD_HASH = hash_password("timing-protection-placeholder")


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
    def __init__(self, db: Session, config: Settings = settings) -> None:
        self.repository = UserRepository(db)
        self.config = config

    def list(self) -> list[UserRead]:
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
        if not self.config.self_registration_enabled:
            raise AppError(
                code="users.self_registration_disabled",
                message="El registro publico esta deshabilitado.",
                status_code=403,
            )
        email = payload.email.strip().lower()
        if not email.endswith("@ucompensar.edu.co"):
            raise AppError(
                code="users.invalid_institutional_email",
                message="Solo se permiten correos institucionales @ucompensar.edu.co.",
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
        user = self.repository.get_by_email(payload.email.strip().lower())
        password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
        password_is_valid = verify_password(payload.password, password_hash)
        if user is None or user.status != "Activo" or not password_is_valid:
            raise AppError(
                code="users.invalid_credentials",
                message="Credenciales invalidas o usuario inactivo.",
                status_code=401,
            )
        if password_needs_rehash(user.password_hash):
            user.password_hash = hash_password(payload.password)
            self.repository.update(user)
        return LoginResponse(
            access_token=create_access_token(user.id),
            token_type="bearer",
            user=to_read_model(user),
        )


def bootstrap_superadmin(
    db: Session,
    config: Settings = settings,
) -> Literal["created", "disabled", "exists"]:
    if not config.bootstrap_superadmin_enabled:
        return "disabled"
    email = (config.bootstrap_superadmin_email or "").strip().lower()
    if UserRepository(db).get_by_email(email):
        return "exists"
    UserService(db, config).create(
        UserCreate(
            name=config.bootstrap_superadmin_name or "",
            email=email,
            role="Super administrador",
            status="Activo",
            password=config.bootstrap_superadmin_password or "",
            permissions=ALL_PERMISSIONS,
        )
    )
    return "created"

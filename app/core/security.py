from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.usuarios.models import User

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/usuarios/login")
token_dependency = Annotated[str, Depends(oauth2_scheme)]
db_dependency = Annotated[Session, Depends(get_db)]


def create_access_token(user_id: str) -> str:
    issued_at = datetime.now(UTC)
    expire = issued_at + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": issued_at,
        "jti": str(uuid4()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def get_current_user(
    token: token_dependency,
    db: db_dependency,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la autenticación.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )

        user_id = payload.get("sub")

        if not user_id:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception from None

    user = db.get(User, user_id)

    if user is None:
        raise credentials_exception

    if user.status != "Activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario está inactivo.",
        )

    return user


def require_permission(permission: str) -> Callable[[User], User]:
    def permission_dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role == "Super administrador":
            return current_user

        if permission not in (current_user.permissions or []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta operación.",
            )

        return current_user

    return permission_dependency


def require_superadmin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "Super administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación requiere permisos de superadministrador.",
        )

    return current_user

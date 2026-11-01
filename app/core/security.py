import logging
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppError
from app.modules.usuarios.models import APPLICATION_NAMES, ApplicationCode, User
from app.modules.usuarios.services.session_service import SessionService

db_dependency = Annotated[Session, Depends(get_db)]
logger = logging.getLogger("researchhub.security")


# El prefijo __Host- exige Secure, Path=/ y sin Domain en el navegador.
SECURE_SESSION_COOKIE = "__Host-researchhub_session"
PLAIN_SESSION_COOKIE = "researchhub_session"


def session_cookie_is_secure(request: Request) -> bool:
    """Marca la cookie Secure solo cuando la peticion llega por HTTPS.

    Un navegador descarta una cookie Secure recibida por HTTP y nadie podria iniciar
    sesion. Asi el login funciona mientras produccion se sirve por HTTP y la cookie
    pasa a Secure sola cuando el proxy entregue HTTPS (con FORWARDED_ALLOW_IPS).
    """
    return settings.session_cookie_secure and request.url.scheme == "https"


def read_session_token(request: Request) -> str | None:
    token = request.cookies.get(SECURE_SESSION_COOKIE) or request.cookies.get(
        PLAIN_SESSION_COOKIE
    )
    # Los tokens emitidos tienen 43 caracteres; se descarta cualquier valor anomalo.
    if not token or len(token) > 128:
        return None
    return token


def set_session_cookie(request: Request, response: Response, token: str) -> None:
    secure = session_cookie_is_secure(request)
    if settings.is_production and not secure:
        logger.warning("session_cookie_without_https")
    response.set_cookie(
        key=SECURE_SESSION_COOKIE if secure else PLAIN_SESSION_COOKIE,
        value=token,
        max_age=settings.session_max_hours * 3600,
        path="/",
        secure=secure,
        httponly=True,
        samesite="strict",
    )


def clear_session_cookie(response: Response) -> None:
    for name in (SECURE_SESSION_COOKIE, PLAIN_SESSION_COOKIE):
        response.delete_cookie(
            key=name,
            path="/",
            secure=name == SECURE_SESSION_COOKIE,
            httponly=True,
            samesite="strict",
        )


def get_current_user(request: Request, db: db_dependency) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="La sesión no es válida o expiró. Inicia sesión de nuevo.",
    )

    token = read_session_token(request)
    if token is None:
        raise credentials_exception

    user = SessionService(db).resolve(token)

    if user is None:
        raise credentials_exception

    if user.status != "Activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario está inactivo.",
        )

    return user


def get_optional_user(request: Request, db: db_dependency) -> User | None:
    """Usuario de la sesion si existe y esta activo; si no, visitante anonimo."""
    token = read_session_token(request)
    user = SessionService(db).resolve(token) if token else None
    return user if user is not None and user.status == "Activo" else None


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


def require_application(application: ApplicationCode) -> Callable[[User], User]:
    """Exige que el usuario autenticado tenga acceso a la aplicacion indicada.

    El login es compartido entre aplicaciones; el token no concede acceso por si
    mismo a ninguna de ellas.
    """

    def application_dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if not current_user.has_application(application):
            raise AppError(
                code="auth.application_forbidden",
                message=(
                    f"Tu cuenta no tiene acceso a {APPLICATION_NAMES[application]}."
                ),
                status_code=status.HTTP_403_FORBIDDEN,
                details={"application": application},
            )

        return current_user

    return application_dependency


def require_superadmin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "Super administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operación requiere permisos de superadministrador.",
        )

    return current_user

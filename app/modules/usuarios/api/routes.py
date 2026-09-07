from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.modules.usuarios.models import User
from app.modules.usuarios.schemas.user import (
    LoginResponse,
    UserCreate,
    UserLogin,
    UserRead,
    UserRegister,
    UserUpdate,
)
from app.modules.usuarios.services import UserService

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
)

db_dependency = Depends(get_db)


def get_user_service(
    db: Session = db_dependency,
) -> UserService:
    return UserService(db)


user_service_dependency = Depends(get_user_service)

current_user_dependency = Annotated[
    User,
    Depends(get_current_user),
]


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: UserLogin,
    service: UserService = user_service_dependency,
) -> LoginResponse:
    return service.authenticate(payload)

@router.post(
    "/registro",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserRegister,
    service: UserService = user_service_dependency,
) -> UserRead:
    return service.register(payload)

@router.get(
    "/me",
    response_model=UserRead,
)
def get_me(
    current_user: current_user_dependency,
) -> UserRead:
    return UserRead(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        status=current_user.status,
        permissions=list(current_user.permissions or []),
    )


@router.get(
    "",
    response_model=list[UserRead],
)
def list_users(
    service: UserService = user_service_dependency,
    _: User = Depends(require_permission("users:read")),
) -> list[UserRead]:
    return service.list()


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    service: UserService = user_service_dependency,
    _: User = Depends(require_permission("users:create")),
) -> UserRead:
    return service.create(payload)


@router.put(
    "/{user_id}",
    response_model=UserRead,
)
def update_user(
    user_id: str,
    payload: UserUpdate,
    service: UserService = user_service_dependency,
    _: User = Depends(require_permission("users:update")),
) -> UserRead:
    return service.update(user_id, payload)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: str,
    service: UserService = user_service_dependency,
    _: User = Depends(require_permission("users:delete")),
) -> Response:
    service.delete(user_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    clear_session_cookie,
    get_current_user,
    read_session_token,
    require_permission,
    set_session_cookie,
)
from app.modules.usuarios.models import User
from app.modules.usuarios.schemas.user import (
    LoginResponse,
    UserCreate,
    UserLogin,
    UserRead,
    UserRegister,
    UserUpdate,
)
from app.modules.usuarios.services import SessionService, UserService
from app.modules.usuarios.services.user_service import to_read_model

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
users_read_dependency = Depends(require_permission("users:read"))
users_create_dependency = Depends(require_permission("users:create"))
users_update_dependency = Depends(require_permission("users:update"))
users_delete_dependency = Depends(require_permission("users:delete"))


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: UserLogin,
    response: Response,
    service: UserService = user_service_dependency,
) -> LoginResponse:
    login_response, token = service.authenticate(payload)
    set_session_cookie(response, token)
    return login_response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: Request,
    db: Session = db_dependency,
) -> Response:
    token = read_session_token(request)
    if token is not None:
        SessionService(db).revoke(token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookie(response)
    return response


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
    return to_read_model(current_user)


@router.get(
    "",
    response_model=list[UserRead],
)
def list_users(
    service: UserService = user_service_dependency,
    _: User = users_read_dependency,
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
    actor: User = users_create_dependency,
) -> UserRead:
    return service.create(payload, actor_id=actor.id)


@router.put(
    "/{user_id}",
    response_model=UserRead,
)
def update_user(
    user_id: str,
    payload: UserUpdate,
    service: UserService = user_service_dependency,
    actor: User = users_update_dependency,
) -> UserRead:
    return service.update(user_id, payload, actor_id=actor.id)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: str,
    service: UserService = user_service_dependency,
    _: User = users_delete_dependency,
) -> Response:
    service.delete(user_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

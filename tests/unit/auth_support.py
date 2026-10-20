from app.modules.usuarios.schemas.user import UserCreate
from app.modules.usuarios.services.user_service import UserService
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm import Session, sessionmaker

PASSWORD = "Clave-institucional-2026"


def create_user(
    session_factory: sessionmaker[Session],
    email: str,
    applications: list[str],
    role: str = "Docente",
) -> str:
    with session_factory() as db:
        user = UserService(db).create(
            UserCreate(
                name="Persona investigadora",
                email=email,
                role=role,
                password=PASSWORD,
                applications=applications,  # type: ignore[arg-type]
            )
        )
        return user.id


def login(
    client: TestClient,
    email: str,
    application: str | None = None,
    password: str = PASSWORD,
) -> Response:
    payload: dict[str, str] = {"email": email, "password": password}
    if application:
        payload["application"] = application
    return client.post("/api/v1/usuarios/login", json=payload)

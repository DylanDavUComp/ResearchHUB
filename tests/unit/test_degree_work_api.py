from collections.abc import Generator

import pytest
from app.core.database import Base, get_db
from app.core.security import get_current_user
from app.main import app
from app.modules.usuarios.models import User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture
def degree_work_client() -> Generator[tuple[TestClient, dict[str, User]], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    users = {
        "student": User(
            id="student-1",
            name="Estudiante",
            email="student-1@ucompensar.edu.co",
            role="Estudiante",
            status="Activo",
            password_hash="not-used",
            permissions=[],
        ),
        "superadmin": User(
            id="super-1",
            name="Super administrador",
            email="super-1@ucompensar.edu.co",
            role="Super administrador",
            status="Activo",
            password_hash="not-used",
            permissions=[],
        ),
    }

    def override_db() -> Generator[Session, None, None]:
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, users
    app.dependency_overrides.clear()


def test_modalities_require_authentication(degree_work_client) -> None:
    client, _ = degree_work_client

    response = client.get("/api/v1/degree-work-modalities")

    assert response.status_code == 401


def test_student_sees_only_active_modalities(degree_work_client) -> None:
    client, users = degree_work_client
    app.dependency_overrides[get_current_user] = lambda: users["student"]

    response = client.get("/api/v1/degree-work-modalities")

    assert response.status_code == 200
    assert len(response.json()) == 9
    assert all(item["status"] == "ACTIVE" for item in response.json())


def test_only_superadmin_can_include_inactive_modalities(degree_work_client) -> None:
    client, users = degree_work_client
    app.dependency_overrides[get_current_user] = lambda: users["student"]

    forbidden = client.get(
        "/api/v1/degree-work-modalities", params={"include_inactive": True}
    )

    app.dependency_overrides[get_current_user] = lambda: users["superadmin"]
    allowed = client.get(
        "/api/v1/degree-work-modalities", params={"include_inactive": True}
    )

    assert forbidden.status_code == 403
    assert allowed.status_code == 200
    assert len(allowed.json()) == 10


def test_student_creates_case_from_active_modality(degree_work_client) -> None:
    client, users = degree_work_client
    app.dependency_overrides[get_current_user] = lambda: users["student"]

    response = client.post(
        "/api/v1/degree-work-cases",
        json={
            "modality_code": "PROYECTO_INVESTIGACION",
            "title": "Plataforma para permanencia estudiantil",
            "program": "Ingeniería de software",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["student_id"] == "student-1"
    assert payload["current_step"]["code"] == "SELECTION"
    assert payload["progress_percent"] == 0

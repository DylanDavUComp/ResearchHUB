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
def client_and_users() -> Generator[tuple[TestClient, dict[str, User]], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    users = {
        key: User(
            id=key,
            name=key,
            email=f"{key}@ucompensar.edu.co",
            role=role,
            status="Activo",
            password_hash="unused",
            permissions=[],
        )
        for key, role in (
            ("student", "Estudiante"),
            ("other", "Estudiante"),
            ("director", "Director de programa"),
            ("superadmin", "Super administrador"),
        )
    }
    with Session(engine, expire_on_commit=False) as db:
        db.add_all(users.values())
        db.commit()

    def override_db() -> Generator[Session, None, None]:
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, users
    app.dependency_overrides.clear()


def as_user(users: dict[str, User], key: str) -> None:
    app.dependency_overrides[get_current_user] = lambda: users[key]


def test_first_four_stages_require_responsible_actors_and_record_history(
    client_and_users: tuple[TestClient, dict[str, User]],
) -> None:
    client, users = client_and_users
    as_user(users, "student")
    created = client.post(
        "/api/v1/semillero-applications",
        json={
            "semillero_name": "Semillero de analitica aplicada",
            "project_title": "Analisis de permanencia estudiantil",
            "program": "Ingenieria de sistemas",
        },
        headers={"Idempotency-Key": "submit-1"},
    )
    assert created.status_code == 201
    item = created.json()
    assert item["current_stage"] == 2
    assert item["completed_stages"] == [1]
    assert (
        client.post(
            f"/api/v1/semillero-applications/{item['id']}/register",
            json={"expected_version": 1, "reference": "Registro institucional 2026-10"},
            headers={"Idempotency-Key": "register-1"},
        ).status_code
        == 403
    )

    as_user(users, "superadmin")
    assigned = client.post(
        f"/api/v1/semillero-applications/{item['id']}/reviewer",
        json={"expected_version": 1, "reviewer_id": "director"},
        headers={"Idempotency-Key": "assign-1"},
    )
    assert assigned.status_code == 200
    as_user(users, "director")
    registered = client.post(
        f"/api/v1/semillero-applications/{item['id']}/register",
        json={"expected_version": 2, "reference": "Registro institucional 2026-10"},
        headers={"Idempotency-Key": "register-1"},
    )
    assert registered.status_code == 200
    assert registered.json()["current_stage"] == 3
    assert (
        client.post(
            f"/api/v1/semillero-applications/{item['id']}/validate",
            json={
                "expected_version": 3,
                "eligible": True,
                "semester": 3,
                "comment": "Requisitos revisados",
            },
            headers={"Idempotency-Key": "validate-invalid"},
        ).status_code
        == 422
    )
    validated = client.post(
        f"/api/v1/semillero-applications/{item['id']}/validate",
        json={
            "expected_version": 3,
            "eligible": True,
            "semester": 4,
            "comment": "Requisitos revisados",
        },
        headers={"Idempotency-Key": "validate-1"},
    )
    assert validated.status_code == 200
    assert validated.json()["current_stage"] == 4

    as_user(users, "student")
    plan = client.post(
        f"/api/v1/semillero-applications/{item['id']}/plan",
        json={
            "expected_version": 4,
            "summary": "Analizar permanencia mediante datos anonimizados.",
            "deliverables": "Informe y conjunto de indicadores",
            "planned_hours": 60,
        },
        headers={"Idempotency-Key": "plan-submit-1"},
    )
    assert plan.status_code == 200
    assert plan.json()["plan_status"] == "SUBMITTED"
    assert plan.json()["current_stage"] == 4
    as_user(users, "director")
    approved = client.post(
        f"/api/v1/semillero-applications/{item['id']}/plan-decision",
        json={"expected_version": 5, "approved": True, "comment": "Plan revisado"},
        headers={"Idempotency-Key": "plan-approve-1"},
    )
    assert approved.status_code == 200
    assert approved.json()["completed_stages"] == [1, 2, 3, 4]
    assert [e["action"] for e in approved.json()["history"]] == [
        "SUBMIT",
        "ASSIGN_REVIEWER",
        "REGISTER",
        "VALIDATE",
        "SUBMIT_PLAN",
        "APPROVE_PLAN",
    ]
    as_user(users, "student")
    original = client.post(
        "/api/v1/semillero-applications",
        json={
            "semillero_name": "Semillero de analitica aplicada",
            "project_title": "Analisis de permanencia estudiantil",
            "program": "Ingenieria de sistemas",
        },
        headers={"Idempotency-Key": "submit-1"},
    )
    assert original.json()["current_stage"] == 2
    assert len(original.json()["history"]) == 1


def test_scope_idempotency_and_stale_version(
    client_and_users: tuple[TestClient, dict[str, User]],
) -> None:
    client, users = client_and_users
    as_user(users, "student")
    payload = {
        "semillero_name": "Semillero ciencias",
        "project_title": "Proyecto de ciencias",
        "program": "Ingenieria",
    }
    first = client.post(
        "/api/v1/semillero-applications",
        json=payload,
        headers={"Idempotency-Key": "create-1"},
    )
    assert first.status_code == 201
    assert (
        client.post(
            "/api/v1/semillero-applications",
            json=payload,
            headers={"Idempotency-Key": "create-1"},
        ).json()["id"]
        == first.json()["id"]
    )
    assert (
        client.post(
            "/api/v1/semillero-applications",
            json={**payload, "project_title": "Otro proyecto"},
            headers={"Idempotency-Key": "create-1"},
        ).status_code
        == 422
    )
    as_user(users, "other")
    assert (
        client.get(f"/api/v1/semillero-applications/{first.json()['id']}").status_code
        == 403
    )
    assert client.get("/api/v1/semillero-applications").json()["total_items"] == 0
    as_user(users, "director")
    assert client.get("/api/v1/semillero-applications").json()["total_items"] == 0
    assert (
        client.get(f"/api/v1/semillero-applications/{first.json()['id']}").status_code
        == 403
    )
    as_user(users, "superadmin")
    assigned = client.post(
        f"/api/v1/semillero-applications/{first.json()['id']}/reviewer",
        json={"expected_version": 1, "reviewer_id": "director"},
        headers={"Idempotency-Key": "assign-1"},
    )
    assert assigned.status_code == 200
    as_user(users, "director")
    url = f"/api/v1/semillero-applications/{first.json()['id']}/register"
    result = client.post(
        url,
        json={"expected_version": 2, "reference": "REG-001"},
        headers={"Idempotency-Key": "register-1"},
    )
    assert result.status_code == 200
    assert (
        client.post(
            url,
            json={"expected_version": 2, "reference": "REG-001"},
            headers={"Idempotency-Key": "register-1"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            url,
            json={"expected_version": 2, "reference": "REG-002"},
            headers={"Idempotency-Key": "register-2"},
        ).status_code
        == 409
    )
    assert (
        len(
            client.get(f"/api/v1/semillero-applications/{first.json()['id']}").json()[
                "history"
            ]
        )
        == 3
    )


def test_director_search_is_scoped_and_blank_fields_are_rejected(
    client_and_users: tuple[TestClient, dict[str, User]],
) -> None:
    client, users = client_and_users
    as_user(users, "student")
    assert client.get("/api/v1/semillero-applications/reviewers").status_code == 403
    assert (
        client.post(
            "/api/v1/semillero-applications",
            json={
                "semillero_name": "   ",
                "project_title": "Proyecto válido",
                "program": "Ingeniería",
            },
            headers={"Idempotency-Key": "blank-name"},
        ).status_code
        == 422
    )
    as_user(users, "superadmin")
    directors = client.get("/api/v1/semillero-applications/reviewers?q=director")
    assert directors.status_code == 200
    assert directors.json() == [{"id": "director", "name": "director"}]

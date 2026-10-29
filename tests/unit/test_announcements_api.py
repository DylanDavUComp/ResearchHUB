from collections.abc import Generator

import pytest
from app.core.database import Base, get_db
from app.core.security import get_current_user
from app.main import app
from app.modules.comunicados.models import AnnouncementAuditEvent
from app.modules.usuarios.models import User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

PAYLOAD = {
    "category": "COMUNICADO",
    "title": "Apertura de convocatoria interna de semilleros 2027",
    "summary": "Los semilleros activos pueden postular hasta el 30 de noviembre.",
    "body": "Consulta los términos de referencia y prepara tu propuesta con tu tutor.",
    "link_url": "https://www.ucompensar.edu.co/investigacion",
}


def build_user(user_id: str, role: str) -> User:
    return User(
        id=user_id,
        name=role,
        email=f"{user_id}@ucompensar.edu.co",
        role=role,
        status="Activo",
        password_hash="not-used",
        permissions=[],
    )


@pytest.fixture
def announcements_client() -> Generator[
    tuple[TestClient, dict[str, User], Session], None, None
]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    users = {
        "student": build_user("student-1", "Estudiante"),
        "admin": build_user("admin-1", "Administrador"),
    }
    with Session(engine, expire_on_commit=False) as setup:
        setup.add_all(users.values())
        setup.commit()

    def override_db() -> Generator[Session, None, None]:
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client, Session(engine) as inspector:
        yield client, users, inspector
    app.dependency_overrides.clear()


def act_as(user: User) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


def create_draft(client: TestClient, users: dict[str, User]) -> dict[str, object]:
    act_as(users["admin"])
    response = client.post("/api/v1/admin/announcements", json=PAYLOAD)
    assert response.status_code == 201
    return response.json()


def test_public_feed_is_empty_without_publications(announcements_client) -> None:
    client, _, _ = announcements_client

    response = client.get("/api/v1/announcements")

    assert response.status_code == 200
    assert response.json()["data"] == []
    assert response.json()["total_items"] == 0


def test_management_requires_authentication(announcements_client) -> None:
    client, _, _ = announcements_client

    response = client.get("/api/v1/admin/announcements")

    assert response.status_code == 401


def test_student_cannot_create_announcements(announcements_client) -> None:
    client, users, _ = announcements_client
    act_as(users["student"])

    response = client.post("/api/v1/admin/announcements", json=PAYLOAD)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "announcements.forbidden"


def test_drafts_stay_out_of_the_public_feed(announcements_client) -> None:
    client, users, _ = announcements_client
    create_draft(client, users)

    response = client.get("/api/v1/announcements")

    assert response.json()["total_items"] == 0


def test_publication_lifecycle_is_audited(announcements_client) -> None:
    client, users, inspector = announcements_client
    draft = create_draft(client, users)

    published = client.post(
        f"/api/v1/admin/announcements/{draft['id']}/publication",
        json={"version": draft["version"]},
    )
    feed = client.get("/api/v1/announcements").json()

    assert published.status_code == 200
    assert published.json()["status"] == "PUBLISHED"
    assert feed["total_items"] == 1
    assert feed["data"][0]["title"] == PAYLOAD["title"]
    assert "author_id" not in feed["data"][0]
    assert "status" not in feed["data"][0]

    locked = client.patch(
        f"/api/v1/admin/announcements/{draft['id']}",
        json={**PAYLOAD, "version": published.json()["version"]},
    )
    assert locked.status_code == 409

    withdrawn = client.post(
        f"/api/v1/admin/announcements/{draft['id']}/withdrawal",
        json={"version": published.json()["version"]},
    )
    assert withdrawn.json()["status"] == "WITHDRAWN"
    assert client.get("/api/v1/announcements").json()["total_items"] == 0

    actions = list(
        inspector.scalars(
            select(AnnouncementAuditEvent.action).order_by(
                AnnouncementAuditEvent.created_at
            )
        )
    )
    assert actions == ["CREATE", "PUBLISH", "WITHDRAW"]


def test_stale_version_is_rejected(announcements_client) -> None:
    client, users, _ = announcements_client
    draft = create_draft(client, users)
    updated = client.patch(
        f"/api/v1/admin/announcements/{draft['id']}",
        json={**PAYLOAD, "title": "Título corregido del comunicado", "version": 1},
    )

    stale = client.patch(
        f"/api/v1/admin/announcements/{draft['id']}",
        json={**PAYLOAD, "version": 1},
    )

    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "announcements.version_conflict"


def test_published_announcement_cannot_be_deleted(announcements_client) -> None:
    client, users, _ = announcements_client
    draft = create_draft(client, users)
    client.post(
        f"/api/v1/admin/announcements/{draft['id']}/publication",
        json={"version": draft["version"]},
    )

    response = client.delete(f"/api/v1/admin/announcements/{draft['id']}")

    assert response.status_code == 409


def test_draft_can_be_deleted(announcements_client) -> None:
    client, users, _ = announcements_client
    draft = create_draft(client, users)

    response = client.delete(f"/api/v1/admin/announcements/{draft['id']}")

    assert response.status_code == 204
    assert client.get("/api/v1/admin/announcements").json()["total_items"] == 0


@pytest.mark.parametrize(
    "link_url",
    ["http://www.ucompensar.edu.co", "javascript:alert(1)", "/ruta-relativa"],
)
def test_links_require_absolute_https(announcements_client, link_url) -> None:
    client, users, _ = announcements_client
    act_as(users["admin"])

    response = client.post(
        "/api/v1/admin/announcements", json={**PAYLOAD, "link_url": link_url}
    )

    assert response.status_code == 422


def test_image_requires_alt_text_and_allowed_origin(announcements_client) -> None:
    client, users, _ = announcements_client
    act_as(users["admin"])

    missing_alt = client.post(
        "/api/v1/admin/announcements",
        json={**PAYLOAD, "image_url": "/static/brand/research-blog-flyer-v2.webp"},
    )
    foreign = client.post(
        "/api/v1/admin/announcements",
        json={
            **PAYLOAD,
            "image_url": "https://images.example.com/foto.webp",
            "image_alt": "Estudiantes en laboratorio",
        },
    )
    traversal = client.post(
        "/api/v1/admin/announcements",
        json={**PAYLOAD, "image_url": "/static/../app.py", "image_alt": "Texto"},
    )
    valid = client.post(
        "/api/v1/admin/announcements",
        json={
            **PAYLOAD,
            "image_url": "/static/brand/research-blog-flyer-v2.webp",
            "image_alt": "Estudiantes analizando resultados",
        },
    )

    assert missing_alt.status_code == 422
    assert foreign.status_code == 422
    assert traversal.status_code == 422
    assert valid.status_code == 201
    assert valid.json()["image_alt"] == "Estudiantes analizando resultados"


def test_public_feed_is_paginated_newest_first(announcements_client) -> None:
    client, users, _ = announcements_client
    for index in range(3):
        act_as(users["admin"])
        draft = client.post(
            "/api/v1/admin/announcements",
            json={**PAYLOAD, "title": f"Comunicado institucional {index}"},
        ).json()
        client.post(
            f"/api/v1/admin/announcements/{draft['id']}/publication",
            json={"version": draft["version"]},
        )

    response = client.get("/api/v1/announcements", params={"page_size": 2})

    assert response.json()["total_pages"] == 2
    assert [item["title"] for item in response.json()["data"]] == [
        "Comunicado institucional 2",
        "Comunicado institucional 1",
    ]

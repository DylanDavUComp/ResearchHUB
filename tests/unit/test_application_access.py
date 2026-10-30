import pytest
from app.core.exceptions import AppError
from app.modules.usuarios.models import User, UserApplication
from app.modules.usuarios.schemas.user import UserCreate, UserUpdate
from app.modules.usuarios.services.user_service import (
    UserService,
    create_superadmin,
)
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from tests.unit.auth_support import PASSWORD, create_user, login


@pytest.fixture
def client(auth_client: TestClient) -> TestClient:
    return auth_client


def test_login_to_application_without_access_issues_no_token(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, "hub@ucompensar.edu.co", ["research_hub"])

    response = login(client, "hub@ucompensar.edu.co", "research_os")

    assert response.status_code == 403
    body = response.json()
    assert "access_token" not in body
    assert response.cookies.get("researchhub_session") is None
    assert body["error"]["code"] == "users.application_forbidden"
    assert body["error"]["message"] == "Tu cuenta no tiene acceso a ResearchOS."
    assert body["error"]["details"]["applications"] == ["research_hub"]


def test_wrong_password_never_reveals_application_access(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, "hub@ucompensar.edu.co", ["research_hub"])

    response = client.post(
        "/api/v1/usuarios/login",
        json={
            "email": "hub@ucompensar.edu.co",
            "password": "otra-clave-incorrecta",
            "application": "research_os",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "users.invalid_credentials"


def test_shared_login_session_works_in_both_applications(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(
        session_factory,
        "both@ucompensar.edu.co",
        ["research_hub", "research_os"],
    )

    hub_login = login(client, "both@ucompensar.edu.co", "research_hub")
    workspace = client.get("/api/v1/research-os/workspace")
    modalities = client.get("/api/v1/degree-work-modalities")

    assert hub_login.status_code == 200
    assert hub_login.json()["user"]["applications"] == [
        "research_hub",
        "research_os",
    ]
    assert workspace.status_code == 200
    assert modalities.status_code == 200


def test_login_without_application_keeps_previous_contract(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, "os@ucompensar.edu.co", ["research_os"])

    response = login(client, "os@ucompensar.edu.co")

    assert response.status_code == 200
    assert response.json()["user"]["applications"] == ["research_os"]


def test_research_os_workspace_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/research-os/workspace")

    assert response.status_code == 401


def test_session_from_hub_cannot_open_research_os_without_access(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, "hub@ucompensar.edu.co", ["research_hub"])
    assert login(client, "hub@ucompensar.edu.co", "research_hub").status_code == 200

    response = client.get("/api/v1/research-os/workspace")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "auth.application_forbidden"


def test_research_os_only_user_cannot_use_research_hub_processes(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, "os@ucompensar.edu.co", ["research_os"])
    assert login(client, "os@ucompensar.edu.co", "research_os").status_code == 200

    hub_route = client.get("/api/v1/degree-work-modalities")
    hub_login = login(client, "os@ucompensar.edu.co", "research_hub")

    assert hub_route.status_code == 403
    assert hub_login.status_code == 403


def test_research_os_workspace_publishes_sections_as_unavailable(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, "os@ucompensar.edu.co", ["research_os"])
    assert login(client, "os@ucompensar.edu.co", "research_os").status_code == 200

    response = client.get("/api/v1/research-os/workspace")

    body = response.json()
    assert response.status_code == 200
    assert body["user"]["email"] == "os@ucompensar.edu.co"
    assert "password_hash" not in body["user"]
    assert [section["code"] for section in body["sections"]] == [
        "applied_projects",
        "capabilities",
        "results",
        "transfer",
    ]
    assert all(section["available"] is False for section in body["sections"])


def test_superadmin_reaches_every_application_without_grants(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(
        session_factory,
        "super@ucompensar.edu.co",
        [],
        role="Super administrador",
    )

    response = login(client, "super@ucompensar.edu.co", "research_os")

    assert response.status_code == 200
    assert response.json()["user"]["applications"] == [
        "research_hub",
        "research_os",
    ]


def test_inactive_user_with_access_cannot_log_in(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = create_user(session_factory, "os@ucompensar.edu.co", ["research_os"])
    with session_factory() as db:
        user = db.get(User, user_id)
        assert user is not None
        user.status = "Inactivo"
        db.commit()

    response = login(client, "os@ucompensar.edu.co", "research_os")

    assert response.status_code == 401


def test_unknown_application_is_rejected(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, "hub@ucompensar.edu.co", ["research_hub"])

    response = login(client, "hub@ucompensar.edu.co", "cris")

    assert response.status_code == 422


def test_new_users_get_research_hub_by_default(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        user = UserService(db).create(
            UserCreate(
                name="Persona",
                email="default@ucompensar.edu.co",
                role="Estudiante",
                password=PASSWORD,
            )
        )

    assert user.applications == ["research_hub"]


def test_update_keeps_existing_grants_and_records_new_grantor(
    session_factory: sessionmaker[Session],
) -> None:
    admin_id = create_user(
        session_factory, "admin@ucompensar.edu.co", ["research_hub"], "Administrador"
    )
    user_id = create_user(session_factory, "doc@ucompensar.edu.co", ["research_hub"])
    with session_factory() as db:
        original = db.scalar(
            select(UserApplication).where(UserApplication.user_id == user_id)
        )
        assert original is not None
        original_granted_at = original.granted_at

    with session_factory() as db:
        updated = UserService(db).update(
            user_id,
            UserUpdate(
                name="Persona investigadora",
                email="doc@ucompensar.edu.co",
                role="Docente",
                applications=["research_hub", "research_os"],
            ),
            actor_id=admin_id,
        )

    with session_factory() as db:
        grants = {
            grant.application: grant
            for grant in db.scalars(
                select(UserApplication).where(UserApplication.user_id == user_id)
            )
        }

    assert updated.applications == ["research_hub", "research_os"]
    assert grants["research_hub"].granted_at == original_granted_at
    assert grants["research_os"].granted_by_id == admin_id


def test_update_without_applications_keeps_current_access(
    session_factory: sessionmaker[Session],
) -> None:
    user_id = create_user(
        session_factory, "doc@ucompensar.edu.co", ["research_hub", "research_os"]
    )

    with session_factory() as db:
        updated = UserService(db).update(
            user_id,
            UserUpdate(
                name="Nombre actualizado",
                email="doc@ucompensar.edu.co",
                role="Docente",
            ),
        )

    assert updated.applications == ["research_hub", "research_os"]


def test_update_can_revoke_application_access(
    session_factory: sessionmaker[Session],
) -> None:
    user_id = create_user(
        session_factory, "doc@ucompensar.edu.co", ["research_hub", "research_os"]
    )

    with session_factory() as db:
        updated = UserService(db).update(
            user_id,
            UserUpdate(
                name="Persona investigadora",
                email="doc@ucompensar.edu.co",
                role="Docente",
                applications=["research_os"],
            ),
        )

    assert updated.applications == ["research_os"]


@pytest.mark.parametrize(
    "applications",
    [["research_os"], ["research_hub", "research_os"], []],
)
def test_admin_cannot_change_own_application_access(
    session_factory: sessionmaker[Session],
    applications: list[str],
) -> None:
    admin_id = create_user(
        session_factory, "admin@ucompensar.edu.co", ["research_hub"], "Administrador"
    )

    with session_factory() as db, pytest.raises(AppError) as error:
        UserService(db).update(
            admin_id,
            UserUpdate(
                name="Administrador",
                email="admin@ucompensar.edu.co",
                role="Administrador",
                applications=applications,  # type: ignore[arg-type]
            ),
            actor_id=admin_id,
        )

    assert error.value.code == "users.self_access_change"


def test_admin_can_save_own_profile_with_unchanged_access(
    session_factory: sessionmaker[Session],
) -> None:
    admin_id = create_user(
        session_factory, "admin@ucompensar.edu.co", ["research_os"], "Administrador"
    )

    with session_factory() as db:
        updated = UserService(db).update(
            admin_id,
            UserUpdate(
                name="Nombre corregido",
                email="admin@ucompensar.edu.co",
                role="Administrador",
                applications=["research_os"],
            ),
            actor_id=admin_id,
        )

    assert updated.name == "Nombre corregido"
    assert updated.applications == ["research_os"]


def test_deleting_user_removes_its_grants(
    session_factory: sessionmaker[Session],
) -> None:
    user_id = create_user(
        session_factory, "doc@ucompensar.edu.co", ["research_hub", "research_os"]
    )

    with session_factory() as db:
        UserService(db).delete(user_id)

    with session_factory() as db:
        remaining = list(
            db.scalars(
                select(UserApplication).where(UserApplication.user_id == user_id)
            )
        )

    assert remaining == []


def test_created_superadmin_receives_both_applications(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        result = create_superadmin(
            db,
            "Super administrador",
            "root@ucompensar.edu.co",
            "Clave-super-segura-2026",
        )
        grants = sorted(
            grant.application for grant in db.scalars(select(UserApplication))
        )

    assert result == "created"
    assert grants == ["research_hub", "research_os"]

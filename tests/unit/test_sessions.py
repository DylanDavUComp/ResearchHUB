from datetime import UTC, datetime, timedelta

import pytest
from app.core.config import Settings, settings
from app.modules.usuarios.models import LoginAttempt, User, UserSession
from app.modules.usuarios.schemas.user import UserUpdate
from app.modules.usuarios.services.user_service import UserService
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker
from tests.unit.auth_support import PASSWORD, create_user, login

COOKIE = "researchhub_session"
EMAIL = "persona@ucompensar.edu.co"


@pytest.fixture
def client(auth_client: TestClient) -> TestClient:
    return auth_client


def stored_sessions(session_factory: sessionmaker[Session]) -> list[UserSession]:
    with session_factory() as db:
        return list(db.scalars(select(UserSession)))


def test_login_sets_httponly_strict_cookie_without_token_in_body(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, EMAIL, ["research_hub"])

    response = login(client, EMAIL, "research_hub")

    set_cookie = response.headers["set-cookie"].lower()
    assert response.status_code == 200
    assert "access_token" not in response.json()
    assert "httponly" in set_cookie
    assert "samesite=strict" in set_cookie
    assert "path=/" in set_cookie


def test_database_stores_only_a_digest_of_the_session_token(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, EMAIL, ["research_hub"])

    response = login(client, EMAIL)

    token = response.cookies[COOKIE]
    sessions = stored_sessions(session_factory)
    assert len(sessions) == 1
    assert sessions[0].token_digest != token
    assert token not in sessions[0].token_digest
    assert len(sessions[0].token_digest) == 64


def test_cookie_over_https_uses_secure_host_prefix(
    client: TestClient,
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_user(session_factory, EMAIL, ["research_hub"])
    monkeypatch.setattr(settings, "session_cookie_secure", True)
    client.base_url = "https://testserver"  # type: ignore[assignment]

    response = login(client, EMAIL)

    set_cookie = response.headers["set-cookie"].lower()
    assert set_cookie.startswith("__host-researchhub_session=")
    assert "secure" in set_cookie
    assert client.get("/api/v1/usuarios/me").status_code == 200


def test_cookie_over_http_is_kept_by_the_browser_until_https_exists(
    client: TestClient,
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Produccion servida por HTTP: una cookie Secure se descartaria y nadie entraria.
    create_user(session_factory, EMAIL, ["research_hub"])
    monkeypatch.setattr(settings, "session_cookie_secure", True)

    response = login(client, EMAIL)

    set_cookie = response.headers["set-cookie"].lower()
    assert set_cookie.startswith(f"{COOKIE}=")
    assert "secure" not in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=strict" in set_cookie
    assert client.get("/api/v1/usuarios/me").status_code == 200


def test_logout_clears_both_cookie_names(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, EMAIL, ["research_hub"])
    login(client, EMAIL)

    response = client.post("/api/v1/usuarios/logout")

    cleared = response.headers.get_list("set-cookie")
    assert any(c.startswith("__Host-researchhub_session=") for c in cleared)
    assert any(c.startswith(f"{COOKIE}=") for c in cleared)
    assert client.get("/api/v1/usuarios/me").status_code == 401


def test_requests_without_session_cookie_are_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/usuarios/me")

    assert response.status_code == 401


def test_bearer_tokens_are_no_longer_accepted(client: TestClient) -> None:
    response = client.get(
        "/api/v1/usuarios/me",
        headers={"Authorization": "Bearer cualquier-valor"},
    )

    assert response.status_code == 401


def test_session_cookie_identifies_the_user(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, EMAIL, ["research_hub"])
    login(client, EMAIL)

    response = client.get("/api/v1/usuarios/me")

    assert response.status_code == 200
    assert response.json()["email"] == EMAIL


def test_logout_revokes_the_session_on_the_server(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, EMAIL, ["research_hub"])
    token = login(client, EMAIL).cookies[COOKIE]

    logout = client.post("/api/v1/usuarios/logout")
    client.cookies.set(COOKIE, token)
    reused = client.get("/api/v1/usuarios/me")

    assert logout.status_code == 204
    assert reused.status_code == 401
    assert stored_sessions(session_factory)[0].revoked_reason == "logout"


def test_logout_without_session_is_harmless(client: TestClient) -> None:
    assert client.post("/api/v1/usuarios/logout").status_code == 204


@pytest.mark.parametrize(
    ("column", "age"),
    [
        ("last_used_at", timedelta(minutes=31)),
        ("expires_at", timedelta(seconds=1)),
    ],
)
def test_idle_and_expired_sessions_are_rejected(
    client: TestClient,
    session_factory: sessionmaker[Session],
    column: str,
    age: timedelta,
) -> None:
    create_user(session_factory, EMAIL, ["research_hub"])
    login(client, EMAIL)
    with session_factory() as db:
        db.execute(
            update(UserSession).values({column: datetime.now(UTC) - age})
        )
        db.commit()

    response = client.get("/api/v1/usuarios/me")

    assert response.status_code == 401


def test_unknown_session_value_is_rejected(client: TestClient) -> None:
    client.cookies.set(COOKIE, "valor-inventado")

    assert client.get("/api/v1/usuarios/me").status_code == 401


@pytest.mark.parametrize(
    "change",
    [
        {"status": "Inactivo"},
        {"password": "Nueva-clave-institucional-2026"},
    ],
)
def test_deactivation_or_password_change_revokes_sessions(
    client: TestClient,
    session_factory: sessionmaker[Session],
    change: dict[str, str],
) -> None:
    user_id = create_user(session_factory, EMAIL, ["research_hub"])
    login(client, EMAIL)

    with session_factory() as db:
        UserService(db).update(
            user_id,
            UserUpdate(
                name="Persona investigadora",
                email=EMAIL,
                role="Docente",
                **change,  # type: ignore[arg-type]
            ),
        )

    assert client.get("/api/v1/usuarios/me").status_code == 401


def test_deleting_user_revokes_sessions(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = create_user(session_factory, EMAIL, ["research_hub"])
    login(client, EMAIL)

    with session_factory() as db:
        UserService(db).delete(user_id)

    assert client.get("/api/v1/usuarios/me").status_code == 401


def test_repeated_failures_lock_the_account_even_with_right_password(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, EMAIL, ["research_hub"])
    failures = [
        login(client, EMAIL, password="clave-equivocada-123").status_code
        for _ in range(settings.login_max_failed_attempts)
    ]

    locked = login(client, EMAIL, password=PASSWORD)

    assert failures == [401] * settings.login_max_failed_attempts
    assert locked.status_code == 429
    assert locked.json()["error"]["code"] == "users.too_many_attempts"
    assert COOKIE not in locked.cookies


def test_lockout_also_applies_to_unknown_emails(client: TestClient) -> None:
    for _ in range(settings.login_max_failed_attempts):
        login(client, "nadie@ucompensar.edu.co", password="clave-equivocada-123")

    response = login(client, "nadie@ucompensar.edu.co", password=PASSWORD)

    assert response.status_code == 429


def test_failed_attempts_never_store_the_email(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    login(client, EMAIL, password="clave-equivocada-123")

    with session_factory() as db:
        attempts = list(db.scalars(select(LoginAttempt)))

    assert len(attempts) == 1
    assert EMAIL not in attempts[0].email_digest
    assert len(attempts[0].email_digest) == 64


def test_successful_login_clears_failed_attempts(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, EMAIL, ["research_hub"])
    for _ in range(settings.login_max_failed_attempts - 1):
        login(client, EMAIL, password="clave-equivocada-123")

    assert login(client, EMAIL).status_code == 200
    with session_factory() as db:
        assert list(db.scalars(select(LoginAttempt))) == []


def test_api_writes_require_the_application_header(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_user(session_factory, EMAIL, ["research_hub"])

    response = client.post(
        "/api/v1/usuarios/login",
        json={"email": EMAIL, "password": PASSWORD},
        headers={"X-Requested-With": ""},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "security.csrf_header_required"
    assert stored_sessions(session_factory) == []


def test_reads_do_not_require_the_application_header(client: TestClient) -> None:
    response = client.get("/api/v1/meta", headers={"X-Requested-With": ""})

    assert response.status_code == 200


def test_inactive_user_session_cannot_be_used(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = create_user(session_factory, EMAIL, ["research_hub"])
    login(client, EMAIL)
    with session_factory() as db:
        user = db.get(User, user_id)
        assert user is not None
        user.status = "Inactivo"
        db.commit()

    assert client.get("/api/v1/usuarios/me").status_code == 403


@pytest.mark.parametrize(
    "database_url",
    [
        "sqlite:///researchhub.db",
        "sqlite://",
        "mysql+pymysql://user:pass@db/researchhub",
    ],
)
def test_settings_only_accept_postgresql(database_url: str) -> None:
    with pytest.raises(ValidationError):
        Settings(database_url=database_url, _env_file=None)  # type: ignore[call-arg]

from fastapi.testclient import TestClient


def test_liveness_returns_ok(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-trace-id"]


def test_readiness_returns_ok_when_database_is_ready(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr("app.core.health.database_is_ready", lambda: True)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_returns_503_when_database_is_not_ready(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr("app.core.health.database_is_ready", lambda: False)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_meta_uses_versioned_prefix(client: TestClient) -> None:
    response = client.get("/api/v1/meta")

    assert response.status_code == 200
    assert response.json()["service"] == "researchhub-u"


def test_home_dashboard_is_served(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "ResearchHub-U" in response.text
    assert "login-view" in response.text
    assert "settings-section" in response.text
    assert "/static/app.js?v=7" in response.text

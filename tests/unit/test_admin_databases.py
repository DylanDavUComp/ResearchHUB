from app.core.security import require_superadmin
from fastapi.testclient import TestClient


def test_database_catalog_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/admin/databases")

    assert response.status_code == 401


def test_superadmin_can_read_database_catalog(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.modules.admin.api.routes.list_database_tables",
        lambda: [
            {
                "schema": "public",
                "name": "usuarios",
                "type": "table",
                "column_count": 2,
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "email", "type": "VARCHAR", "nullable": False},
                ],
            }
        ],
    )
    client.app.dependency_overrides[require_superadmin] = lambda: object()

    response = client.get("/api/v1/admin/databases")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "read_only"
    assert payload["databases"][0]["name"] == "researchhub_u"
    assert payload["databases"][0]["tables"][0]["name"] == "usuarios"

    client.app.dependency_overrides.clear()

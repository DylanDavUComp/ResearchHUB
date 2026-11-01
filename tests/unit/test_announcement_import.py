import json
import re
from pathlib import Path

import pytest
from app.modules.comunicados.importer import MAX_IMPORT_ITEMS
from app.modules.comunicados.models import Announcement, AnnouncementAuditEvent
from app.modules.usuarios.models import User
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from tests.unit.test_announcements_api import (  # noqa: F401
    act_as,
    announcements_client,
)

ClientFixture = tuple[TestClient, dict[str, User], Session]
SKILL = (
    Path(__file__).resolve().parents[2]
    / "app/web/static/downloads/skill-comunicados-researchhub.md"
)
IMPORT_URL = "/api/v1/admin/announcements/import"


def item(title: str, **extra: object) -> dict[str, object]:
    return {
        "category": "NOTICIA",
        "title": title,
        "summary": "Resumen suficiente para la portada.",
        "content": [{"type": "paragraph", "runs": [{"text": "Texto del comunicado."}]}],
        **extra,
    }


def skill_examples() -> list[object]:
    text = SKILL.read_text(encoding="utf-8")
    return [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.S)]


def count(session: Session, model: type[Announcement | AnnouncementAuditEvent]) -> int:
    session.expire_all()
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


@pytest.fixture
def client(announcements_client: ClientFixture) -> ClientFixture:  # noqa: F811
    act_as(announcements_client[1]["superadmin"])
    return announcements_client


def test_skill_examples_import_without_errors(client: ClientFixture) -> None:
    test_client, _, inspector = client
    examples = skill_examples()
    assert len(examples) == 2

    for example in examples:
        report = test_client.post(IMPORT_URL, params={"dry_run": False}, json=example)
        assert report.status_code == 200, report.text
        assert all(not entry["errors"] for entry in report.json()["items"])

    assert count(inspector, Announcement) == 3


def test_dry_run_reports_without_creating(client: ClientFixture) -> None:
    test_client, _, inspector = client

    report = test_client.post(IMPORT_URL, json=[item("Primer comunicado")]).json()

    assert report == {
        "dry_run": True,
        "total": 1,
        "valid": 1,
        "created": 0,
        "items": [
            {
                "index": 0,
                "title": "Primer comunicado",
                "category": "NOTICIA",
                "blocks": 1,
                "errors": [],
            }
        ],
    }
    assert count(inspector, Announcement) == 0


@pytest.mark.parametrize(
    "payload",
    [
        item("Un solo comunicado"),
        [item("Un solo comunicado")],
        {"announcements": [item("Un solo comunicado")]},
    ],
)
def test_accepts_single_list_and_wrapped_formats(
    client: ClientFixture, payload: object
) -> None:
    test_client, _, inspector = client

    report = test_client.post(IMPORT_URL, params={"dry_run": False}, json=payload)

    assert report.json()["created"] == 1
    assert count(inspector, Announcement) == 1


def test_bulk_import_creates_audited_drafts(client: ClientFixture) -> None:
    test_client, users, inspector = client
    payload = {"announcements": [item(f"Comunicado número {n}") for n in range(5)]}

    report = test_client.post(IMPORT_URL, params={"dry_run": False}, json=payload)

    assert report.json()["created"] == 5
    inspector.expire_all()
    drafts = list(inspector.scalars(select(Announcement)))
    assert {draft.status for draft in drafts} == {"DRAFT"}
    assert {draft.author_id for draft in drafts} == {users["superadmin"].id}
    assert all(draft.published_at is None for draft in drafts)
    assert count(inspector, AnnouncementAuditEvent) == 5


def test_any_error_creates_nothing_and_explains_where(client: ClientFixture) -> None:
    test_client, _, inspector = client
    broken = item(
        "Comunicado con imagen",
        content=[
            {"type": "paragraph", "runs": [{"text": "Bien."}]},
            {"type": "image", "src": "/static/foto.png", "alt": " "},
        ],
        notes="campo inventado",
    )
    payload = [item("Comunicado correcto"), broken]

    response = test_client.post(IMPORT_URL, params={"dry_run": False}, json=payload)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "announcements.import_invalid"
    items = error["details"]["report"]["items"]
    assert items[0]["errors"] == []
    fields = {issue["field"] for issue in items[1]["errors"]}
    assert "Bloque 2 (image) · alt" in fields
    assert "notes" in fields
    assert count(inspector, Announcement) == 0


def test_repeated_titles_are_rejected(client: ClientFixture) -> None:
    test_client, _, _ = client
    test_client.post(IMPORT_URL, params={"dry_run": False}, json=item("Ya existe"))

    report = test_client.post(
        IMPORT_URL, json=[item("Ya existe"), item("Nuevo"), item("NUEVO")]
    ).json()

    messages = [
        [issue["message"] for issue in entry["errors"]] for entry in report["items"]
    ]
    assert messages == [
        ["Ya existe un comunicado con este título."],
        [],
        ["Título repetido en el archivo."],
    ]


def test_uploaded_files_cannot_be_referenced_by_json(client: ClientFixture) -> None:
    test_client, _, _ = client
    asset = "/media/announcements/00000000-0000-4000-8000-000000000000"

    report = test_client.post(
        IMPORT_URL, json=item("Con archivo", image_url=asset, image_alt="Foto")
    ).json()

    assert report["items"][0]["errors"][0]["field"] == "imagenes"


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ([], "announcements.import_empty"),
        (
            [item(f"Comunicado {n}") for n in range(MAX_IMPORT_ITEMS + 1)],
            "announcements.import_too_many",
        ),
    ],
)
def test_import_size_is_bounded(
    client: ClientFixture, payload: object, code: str
) -> None:
    test_client, _, _ = client

    response = test_client.post(IMPORT_URL, json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == code


def test_only_superadmins_import(client: ClientFixture) -> None:
    test_client, users, inspector = client
    act_as(users["admin"])

    response = test_client.post(
        IMPORT_URL, params={"dry_run": False}, json=item("Intento sin permiso")
    )

    assert response.status_code == 403
    assert count(inspector, Announcement) == 0


def test_console_offers_the_skill_download(client: ClientFixture) -> None:
    test_client, _, _ = client

    html = test_client.get("/configuracion").text
    skill = test_client.get("/static/downloads/skill-comunicados-researchhub.md")

    assert 'download="skill-comunicados-researchhub.md"' in html
    assert 'id="import-announcements-button"' in html
    assert "/static/announcement-import.js?v=1" in html
    assert skill.status_code == 200
    assert skill.text.startswith("---\nname: comunicados-researchhub")

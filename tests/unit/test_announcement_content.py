from collections.abc import Generator

import pytest
from app.core.security import get_optional_user
from app.main import app
from app.modules.comunicados.assets import MAX_IMAGE_BYTES
from app.modules.comunicados.models import AnnouncementAsset
from app.modules.usuarios.models import User
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from tests.unit.test_announcements_api import (  # noqa: F401
    PAYLOAD,
    act_as,
    announcements_client,
)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PDF = b"%PDF-1.7\n" + b"0" * 64
ClientFixture = tuple[TestClient, dict[str, User], Session]

RICH_CONTENT: list[dict[str, object]] = [
    {"type": "heading", "level": 2, "runs": [{"text": "Cronograma"}]},
    {
        "type": "paragraph",
        "runs": [
            {"text": "Postula "},
            {"text": "antes del 30", "marks": ["italic", "bold"]},
            {"text": " en "},
            {"text": "el portal", "link": "https://www.ucompensar.edu.co"},
            {"text": ".\nSegunda línea"},
        ],
    },
    {
        "type": "list",
        "style": "ordered",
        "items": [[{"text": "Inscripción"}], [{"text": "Evaluación"}]],
    },
    {"type": "quote", "runs": [{"text": "Investigar es hacer."}], "cite": "Rectoría"},
    {"type": "callout", "tone": "warning", "title": "Cierre", "runs": []},
    {"type": "divider"},
    {"type": "image", "src": "/static/brand/foto.png", "alt": "Equipo", "size": "wide"},
    {
        "type": "gallery",
        "images": [
            {"src": "/static/a.png", "alt": "Uno"},
            {"src": "/static/b.png", "alt": "Dos", "caption": "Laboratorio"},
        ],
    },
    {
        "type": "video",
        "provider": "youtube",
        "video_id": "dQw4w9WgXcQ",
        "title": "Presentación de la convocatoria",
    },
    {"type": "button", "label": "Inscríbete", "url": "https://forms.example.edu.co"},
    {"type": "file", "url": "https://www.ucompensar.edu.co/tdr.pdf", "label": "TdR"},
    {
        "type": "table",
        "header": True,
        "rows": [["Etapa", "Fecha"], ["Cierre", "30 de noviembre"]],
    },
    {
        "type": "event",
        "start_date": "2026-11-30",
        "start_time": "14:00",
        "mode": "hibrido",
        "location": "Sede Av. 68",
        "registration_url": "mailto:investigacion@ucompensar.edu.co",
    },
]


@pytest.fixture
def client(announcements_client: ClientFixture) -> ClientFixture:  # noqa: F811
    return announcements_client


@pytest.fixture(autouse=True)
def anonymous_media() -> Generator[None, None, None]:
    app.dependency_overrides[get_optional_user] = lambda: None
    yield
    app.dependency_overrides.pop(get_optional_user, None)


def view_media_as(user: User | None) -> None:
    app.dependency_overrides[get_optional_user] = lambda: user


def rich_payload(
    content: list[dict[str, object]], **extra: object
) -> dict[str, object]:
    payload: dict[str, object] = {**PAYLOAD, "content": content, **extra}
    payload.pop("body")
    return payload


def upload(client: TestClient, data: bytes, filename: str = "foto.png") -> Response:
    return client.post(
        "/api/v1/admin/announcement-assets",
        params={"filename": filename},
        content=data,
        headers={"Content-Type": "application/octet-stream"},
    )


def test_plain_text_body_becomes_paragraph_blocks(client: ClientFixture) -> None:
    test_client, users, _ = client
    act_as(users["superadmin"])
    payload = {**PAYLOAD, "body": "Primer párrafo.\n\nSegundo párrafo."}

    created = test_client.post("/api/v1/admin/announcements", json=payload).json()

    assert created["content"] == [
        {
            "type": "paragraph",
            "runs": [{"text": "Primer párrafo.", "marks": [], "link": None}],
        },
        {
            "type": "paragraph",
            "runs": [{"text": "Segundo párrafo.", "marks": [], "link": None}],
        },
    ]
    assert created["body"] == "Primer párrafo.\n\nSegundo párrafo."


def test_every_block_type_round_trips_and_derives_plain_text(
    client: ClientFixture,
) -> None:
    test_client, users, _ = client
    act_as(users["superadmin"])

    response = test_client.post(
        "/api/v1/admin/announcements", json=rich_payload(RICH_CONTENT)
    )

    assert response.status_code == 201, response.text
    created = response.json()
    assert [block["type"] for block in created["content"]] == [
        block["type"] for block in RICH_CONTENT
    ]
    assert created["content"][1]["runs"][1]["marks"] == ["bold", "italic"]
    assert created["content"][12]["start_time"] == "14:00:00"
    assert "Cronograma" in created["body"]
    assert "- Inscripción" in created["body"]
    assert "Etapa | Fecha" in created["body"]


@pytest.mark.parametrize(
    "block",
    [
        {"type": "paragraph", "runs": [{"text": "x", "link": "javascript:alert(1)"}]},
        {"type": "paragraph", "runs": [{"text": "x", "link": "http://inseguro.co"}]},
        {"type": "paragraph", "runs": [{"text": "x"}], "html": "<script>"},
        {"type": "paragraph", "runs": [{"text": "x", "marks": ["blink"]}]},
        {"type": "image", "src": "https://evil.example.com/a.png", "alt": "x"},
        {"type": "image", "src": "/static/../secret", "alt": "x"},
        {"type": "image", "src": "/static/a.png", "alt": "   "},
        {"type": "video", "provider": "youtube", "video_id": "bad id!", "title": "V"},
        {"type": "button", "label": "Ir", "url": "data:text/html,hola"},
        {"type": "table", "rows": [["a", "b"], ["c"]]},
        {"type": "event", "start_date": "2026-11-30", "end_date": "2026-11-01"},
        {"type": "iframe", "src": "https://evil.example.com"},
    ],
)
def test_unsafe_or_malformed_blocks_are_rejected(
    client: ClientFixture, block: dict[str, object]
) -> None:
    test_client, users, _ = client
    act_as(users["superadmin"])

    response = test_client.post(
        "/api/v1/admin/announcements", json=rich_payload([block])
    )

    assert response.status_code == 422


def test_content_size_is_bounded(client: ClientFixture) -> None:
    test_client, users, _ = client
    act_as(users["superadmin"])
    blocks: list[dict[str, object]] = [{"type": "divider"}] * 151

    response = test_client.post(
        "/api/v1/admin/announcements", json=rich_payload(blocks)
    )

    assert response.status_code == 422


def test_only_superadmins_upload_files(client: ClientFixture) -> None:
    test_client, users, _ = client
    act_as(users["admin"])

    assert upload(test_client, PNG).status_code == 403


@pytest.mark.parametrize(
    "data",
    [
        b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>",
        b"<html><script>alert(1)</script></html>",
        b"MZ\x90\x00 ejecutable",
    ],
)
def test_upload_rejects_types_that_could_run_code(
    client: ClientFixture, data: bytes
) -> None:
    test_client, users, _ = client
    act_as(users["superadmin"])

    response = upload(test_client, data, "foto.png")

    assert response.status_code == 415


def test_upload_enforces_size_limits(client: ClientFixture) -> None:
    test_client, users, _ = client
    act_as(users["superadmin"])

    image = upload(test_client, PNG + b"0" * MAX_IMAGE_BYTES)
    document = upload(test_client, PDF + b"0" * MAX_IMAGE_BYTES, "tdr.pdf")

    assert image.status_code == 413
    assert document.status_code == 201
    assert document.json()["kind"] == "document"
    assert document.json()["filename"] == "tdr.pdf"


def test_upload_detects_type_from_content_not_name(client: ClientFixture) -> None:
    test_client, users, _ = client
    act_as(users["superadmin"])

    asset = upload(test_client, PNG, "../../etc/passwd.exe").json()

    assert asset["content_type"] == "image/png"
    assert asset["filename"] == "passwd.png"
    assert asset["url"] == f"/media/announcements/{asset['id']}"


def test_files_are_private_until_their_announcement_is_published(
    client: ClientFixture,
) -> None:
    test_client, users, inspector = client
    act_as(users["superadmin"])
    asset = upload(test_client, PNG).json()
    image = {"type": "image", "src": asset["url"], "alt": "Equipo"}

    assert test_client.get(asset["url"]).status_code == 404
    view_media_as(users["superadmin"])
    private = test_client.get(asset["url"])
    assert private.status_code == 200
    assert private.headers["cache-control"] == "private, no-store"
    view_media_as(None)

    created = test_client.post(
        "/api/v1/admin/announcements",
        json=rich_payload([image], image_url=asset["url"], image_alt="Portada"),
    ).json()
    assert test_client.get(asset["url"]).status_code == 404

    test_client.post(
        f"/api/v1/admin/announcements/{created['id']}/publication",
        json={"version": created["version"]},
    )
    public = test_client.get(asset["url"])
    assert public.status_code == 200
    assert public.content == PNG
    assert public.headers["content-type"] == "image/png"
    assert public.headers["cache-control"] == "public, max-age=86400"
    assert "sandbox" in public.headers["content-security-policy"]
    assert public.headers["x-content-type-options"] == "nosniff"
    linked = inspector.get(AnnouncementAsset, asset["id"])
    assert linked is not None and linked.announcement_id == created["id"]


def test_documents_download_instead_of_opening_as_pages(client: ClientFixture) -> None:
    test_client, users, _ = client
    act_as(users["superadmin"])
    view_media_as(users["superadmin"])
    asset = upload(test_client, PDF, "Términos de referencia.pdf").json()

    response = test_client.get(asset["url"])

    disposition = response.headers["content-disposition"]
    assert disposition.startswith("attachment;")
    assert "T%C3%A9rminos%20de%20referencia.pdf" in disposition


def test_a_file_belongs_to_one_announcement(client: ClientFixture) -> None:
    test_client, users, _ = client
    act_as(users["superadmin"])
    asset = upload(test_client, PNG).json()
    image: list[dict[str, object]] = [
        {"type": "image", "src": asset["url"], "alt": "Equipo"}
    ]
    first = test_client.post("/api/v1/admin/announcements", json=rich_payload(image))
    assert first.status_code == 201

    second = test_client.post(
        "/api/v1/admin/announcements",
        json=rich_payload(image, title="Otro comunicado distinto"),
    )

    assert second.status_code == 422
    assert second.json()["error"]["code"] == "announcements.asset_in_use"


def test_missing_file_is_reported(client: ClientFixture) -> None:
    test_client, users, _ = client
    act_as(users["superadmin"])
    missing = "/media/announcements/00000000-0000-4000-8000-000000000000"

    response = test_client.post(
        "/api/v1/admin/announcements",
        json=rich_payload([{"type": "image", "src": missing, "alt": "x"}]),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "announcements.asset_missing"


def test_unused_files_are_removed_on_update_and_delete(client: ClientFixture) -> None:
    test_client, users, inspector = client
    act_as(users["superadmin"])
    kept, dropped = upload(test_client, PNG).json(), upload(test_client, PNG).json()
    blocks: list[dict[str, object]] = [
        {"type": "image", "src": kept["url"], "alt": "Uno"},
        {"type": "image", "src": dropped["url"], "alt": "Dos"},
    ]
    created = test_client.post(
        "/api/v1/admin/announcements", json=rich_payload(blocks)
    ).json()

    updated = test_client.patch(
        f"/api/v1/admin/announcements/{created['id']}",
        json=rich_payload(blocks[:1], version=created["version"]),
    )
    assert updated.status_code == 200

    def stored() -> list[str]:
        inspector.expire_all()
        return list(inspector.scalars(select(AnnouncementAsset.id)))

    assert stored() == [kept["id"]]
    test_client.delete(f"/api/v1/admin/announcements/{created['id']}")
    assert stored() == []


def test_published_announcement_has_a_direct_link(client: ClientFixture) -> None:
    test_client, users, _ = client
    act_as(users["superadmin"])
    created = test_client.post(
        "/api/v1/admin/announcements", json=rich_payload(RICH_CONTENT)
    ).json()
    url = f"/api/v1/announcements/{created['id']}"

    assert test_client.get(url).status_code == 404
    test_client.post(
        f"/api/v1/admin/announcements/{created['id']}/publication",
        json={"version": created["version"]},
    )
    public = test_client.get(url)

    assert public.status_code == 200
    assert public.json()["content"][0]["type"] == "heading"
    assert "status" not in public.json()


def test_pages_allow_only_privacy_friendly_video_players(
    client: ClientFixture,
) -> None:
    test_client, _, _ = client

    policy = test_client.get("/").headers["content-security-policy"]

    assert "frame-src https://www.youtube-nocookie.com https://player.vimeo.com;" in (
        policy
    )
    assert "frame-ancestors 'none'" in policy

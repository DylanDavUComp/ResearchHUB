from app.core.config import settings
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
    assert response.json()["features"]["self_registration"] is False
    assert response.json()["applications"]["research_hub_u"]["available"] is True
    assert response.json()["applications"]["research_os"]["available"] is False
    assert response.json()["applications"]["cris"]["available"] is False
    assert response.json()["applications"]["services_marketplace"] == {
        "available": False,
        "url": None,
    }
    assert response.json()["applications"]["crai"] == {
        "available": True,
        "url": "https://crai.ucompensar.edu.co/",
    }
    assert response.json()["links"]["research_blog"] == {
        "available": False,
        "url": None,
    }


def test_meta_enables_research_os_when_url_is_configured(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(
        settings,
        "research_os_url",
        "https://research-os.example.edu.co",
    )

    response = client.get("/api/v1/meta")

    assert response.json()["applications"]["research_os"] == {
        "available": True,
        "url": "https://research-os.example.edu.co",
    }


def test_meta_enables_cris_when_url_is_configured(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "cris_url", "https://cris.example.edu.co")

    response = client.get("/api/v1/meta")

    assert response.json()["applications"]["cris"] == {
        "available": True,
        "url": "https://cris.example.edu.co",
    }


def test_meta_enables_research_blog_when_url_is_configured(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(
        settings,
        "research_blog_url",
        "https://blog.example.edu.co",
    )

    response = client.get("/api/v1/meta")

    assert response.json()["links"]["research_blog"] == {
        "available": True,
        "url": "https://blog.example.edu.co",
    }


def test_meta_enables_services_marketplace_when_url_is_configured(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(
        settings,
        "services_marketplace_url",
        "https://servicios.example.edu.co",
    )

    response = client.get("/api/v1/meta")

    assert response.json()["applications"]["services_marketplace"] == {
        "available": True,
        "url": "https://servicios.example.edu.co",
    }


def test_responses_include_security_and_cache_headers(client: TestClient) -> None:
    response = client.get("/api/v1/meta")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["cache-control"] == "no-store"
    assert "default-src 'self'" in response.headers["content-security-policy"]


def test_home_dashboard_is_served(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "ResearchHUB" in response.text
    assert "ResarchHUB" not in response.text
    assert "Research<span>HUB</span>" in response.text
    assert "Resarch<span>HUB</span>" not in response.text
    assert "ResearchHub" + "-U" not in response.text
    assert "login-view" in response.text
    assert 'id="app-launcher"' in response.text
    assert 'id="open-researchhub"' in response.text
    assert 'id="open-researchos"' in response.text
    assert 'id="open-cris"' in response.text
    assert 'id="open-crai"' in response.text
    assert 'id="opportunity-carousel"' in response.text
    assert 'id="opportunity-prev"' in response.text
    assert 'id="opportunity-next"' in response.text
    assert 'id="open-research-blog"' in response.text
    assert 'id="services-marketplace"' in response.text
    assert 'id="open-services-marketplace"' in response.text
    assert "Servicios y marketplace" in response.text
    assert "/static/brand/services-marketplace-flyer-v1.png" in response.text
    assert 'data-autoplay-ms="4000"' in response.text
    assert response.text.count("data-opportunity-slide") == 3
    assert "Investigacion formativa" in response.text
    assert "Investigacion aplicada y transferencia" in response.text
    assert "Informacion cientifica institucional" in response.text
    assert "Recursos para el aprendizaje y la investigacion" in response.text
    assert "settings-section" in response.text
    assert "degree-work-section" in response.text
    assert "degree-work-case-form" in response.text
    assert "modality-settings-card" in response.text
    assert 'id="degree-work-journey"' in response.text
    assert 'data-stage="OFFER"' in response.text
    assert 'data-stage="CLOSURE"' in response.text
    assert 'id="journey-step-detail"' in response.text
    assert "/static/styles.css?v=30" in response.text
    assert "/static/app.js?v=17" in response.text
    assert "/static/degree-work.js?v=2" in response.text


def test_launcher_uses_consistent_action_labels(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Ingresar a ResearchHUB <span" not in response.text
    assert 'Ingresar <span aria-hidden="true">&#8594;</span>' in response.text
    assert "No configurado" not in response.text
    assert '<span id="researchos-action-label">Próximamente</span>' in response.text
    assert '<span id="cris-action-label">Próximamente</span>' in response.text
    assert '<span id="crai-action-label">Próximamente</span>' in response.text
    assert (
        response.text.count(
            '<span class="opportunity-link-label">Próximamente</span>'
        )
        == 3
    )

    script = client.get("/static/app.js")
    assert script.status_code == 200
    assert (
        'label.textContent = isAvailable ? "Ingresar" : "Próximamente"'
        in script.text
    )
    assert "Ingresar a ResearchOS" not in script.text
    assert "Ingresar a CRIS" not in script.text
    assert "Ingresar al CRAI" not in script.text
    assert "Leer en el blog" not in script.text
    assert "elements.openServicesMarketplace.addEventListener" in script.text


def test_launcher_has_compact_layout_for_short_laptop_viewports(
    client: TestClient,
) -> None:
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "@media (min-width: 1181px) and (max-height: 700px)" in response.text
    assert "@media (min-width: 1181px) and (max-height: 600px)" in response.text
    assert "grid-template-rows: repeat(2, minmax(0, 1fr));" in response.text
    assert "font-size: 32px;" in response.text


def test_home_uses_the_ucompensar_2026_visual_system(client: TestClient) -> None:
    home = client.get("/")
    stylesheet = client.get("/static/styles.css")

    assert home.status_code == 200
    assert stylesheet.status_code == 200
    assert 'class="institution-name"' in home.text
    assert 'class="product-name"' in home.text
    assert "brand-mark" not in home.text
    assert "La Universidad del Futuro" not in home.text
    assert "SourceSans3-VariableFont_wght.ttf" in stylesheet.text
    assert "Agrandir-Narrow.otf" in stylesheet.text
    assert "#6d20e5" in stylesheet.text.lower()
    assert "#3b0970" in stylesheet.text.lower()
    assert "#ff7000" in stylesheet.text.lower()


def test_launcher_fits_limited_height_desktops_without_scaling(
    client: TestClient,
) -> None:
    stylesheet = client.get("/static/styles.css")

    assert stylesheet.status_code == 200
    assert "@media (min-width: 1181px) and (max-height: 1000px)" in stylesheet.text
    assert "(max-width: 1300px) and (max-height: 1000px)" in stylesheet.text
    assert "height: 100dvh" in stylesheet.text
    assert "grid-template-rows: auto minmax(0, 1fr) auto" in stylesheet.text


def test_home_exposes_responsive_navigation_and_brand_art(client: TestClient) -> None:
    home = client.get("/")
    illustration = client.get("/static/brand/degree-work-journey-v1.png")
    brand_logo = client.get("/static/brand/ucompensar-hacer-para-saber.png")
    blog_flyer = client.get("/static/brand/research-blog-flyer-v1.png")
    opportunities_flyer = client.get(
        "/static/brand/research-opportunities-flyer-v1.png"
    )
    agenda_flyer = client.get("/static/brand/research-agenda-flyer-v1.png")

    assert home.status_code == 200
    assert illustration.status_code == 200
    assert brand_logo.status_code == 200
    assert blog_flyer.status_code == 200
    assert opportunities_flyer.status_code == 200
    assert agenda_flyer.status_code == 200
    assert 'id="mobile-menu-button"' in home.text
    assert 'aria-controls="main-sidebar"' in home.text
    assert 'id="sidebar-backdrop"' in home.text
    assert 'src="/static/brand/degree-work-journey-v1.png"' in home.text
    assert 'class="brand-logo"' in home.text
    assert 'src="/static/brand/ucompensar-hacer-para-saber.png"' in home.text

import pytest
from app.core.config import Settings
from pydantic import ValidationError


def production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": "production",
        "app_debug": False,
        "docs_enabled": False,
        "security_hsts_enabled": True,
        "self_registration_enabled": False,
        "secret_key": "production-secret-with-at-least-32-characters",
        "database_url": (
            "postgresql+pg8000://researchhub_user:strong-password"
            "@db:5432/researchhub_u"
        ),
        "postgres_password": "strong-password",
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("app_debug", True),
        ("docs_enabled", True),
        ("security_hsts_enabled", False),
        ("self_registration_enabled", True),
        ("secret_key", "replace_with_secure_value"),
        ("postgres_password", "change_me"),
    ],
)
def test_production_rejects_unsafe_configuration(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        production_settings(**{field: value})


def test_production_accepts_hardened_configuration() -> None:
    config = production_settings()

    assert config.is_production
    assert config.allowed_host_list == ["localhost", "127.0.0.1", "testserver"]


def test_empty_optional_application_url_is_normalized() -> None:
    config = Settings(services_marketplace_url="", _env_file=None)

    assert config.services_marketplace_url is None


@pytest.mark.parametrize(
    ("field", "http_url", "https_url"),
    [
        (
            "research_os_url",
            "http://research-os.example.edu.co",
            "https://research-os.example.edu.co",
        ),
        (
            "cris_url",
            "http://cris.example.edu.co",
            "https://cris.example.edu.co",
        ),
        (
            "crai_url",
            "http://crai.ucompensar.edu.co/",
            "https://crai.ucompensar.edu.co/",
        ),
        (
            "research_blog_url",
            "http://blog.example.edu.co",
            "https://blog.example.edu.co",
        ),
        (
            "services_marketplace_url",
            "http://servicios.example.edu.co",
            "https://servicios.example.edu.co",
        ),
    ],
)
def test_production_application_urls_require_https(
    field: str, http_url: str, https_url: str
) -> None:
    with pytest.raises(ValidationError):
        production_settings(**{field: http_url})

    config = production_settings(**{field: https_url})
    assert getattr(config, field) == https_url


def test_bootstrap_requires_complete_strong_credentials() -> None:
    with pytest.raises(ValidationError):
        Settings(
            bootstrap_superadmin_enabled=True,
            bootstrap_superadmin_email="operator@ucompensar.edu.co",
            bootstrap_superadmin_password="short",
            secret_key="a-secure-local-secret-with-at-least-32-characters",
            _env_file=None,
        )

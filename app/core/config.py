from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ResearchHUB"
    app_version: str = "0.1.0"
    app_env: str = "local"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    service_name: str = "researchhub-u"
    cris_url: str | None = None
    crai_url: str | None = "https://crai.ucompensar.edu.co/"
    research_blog_url: str | None = None
    services_marketplace_url: str | None = None

    postgres_db: str = "researchhub_u"
    postgres_user: str = "researchhub_user"
    postgres_password: str = "change_me"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str = Field(
        default="postgresql+pg8000://researchhub_user:change_me@localhost:5432/researchhub_u"
    )
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=200)
    database_pool_timeout_seconds: int = Field(default=30, ge=1, le=300)
    database_pool_recycle_seconds: int = Field(default=1800, ge=60)

    # Clave HMAC para las huellas de sesion e intentos de login guardadas en
    # PostgreSQL. Cambiarla invalida todas las sesiones activas.
    secret_key: str = "replace_with_secure_value_at_least_32_chars"
    session_idle_minutes: int = Field(default=30, ge=5, le=240)
    session_max_hours: int = Field(default=12, ge=1, le=24)
    # Secure cuando la peticion llega por HTTPS; en local sin HTTPS va en false.
    session_cookie_secure: bool = True
    login_max_failed_attempts: int = Field(default=5, ge=3, le=20)
    login_lockout_minutes: int = Field(default=15, ge=1, le=1440)
    log_level: str = "INFO"
    docs_enabled: bool = True
    self_registration_enabled: bool = False
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    cors_origins: str = ""
    announcement_image_origins: str = ""
    security_hsts_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @property
    def allowed_host_list(self) -> list[str]:
        return [
            value.strip() for value in self.allowed_hosts.split(",") if value.strip()
        ]

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            value.strip() for value in self.cors_origins.split(",") if value.strip()
        ]

    @property
    def announcement_image_origin_list(self) -> list[str]:
        return [
            value.strip().rstrip("/")
            for value in self.announcement_image_origins.split(",")
            if value.strip()
        ]

    @field_validator(
        "cris_url",
        "crai_url",
        "research_blog_url",
        "services_marketplace_url",
        mode="before",
    )
    @classmethod
    def normalize_optional_url(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def validate_operational_safety(self) -> "Settings":
        application_urls = {
            "CRIS_URL": self.cris_url,
            "CRAI_URL": self.crai_url,
            "RESEARCH_BLOG_URL": self.research_blog_url,
            "SERVICES_MARKETPLACE_URL": self.services_marketplace_url,
        }
        for setting_name, application_url in application_urls.items():
            if not application_url:
                continue
            parsed_url = urlsplit(application_url)
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
                raise ValueError(f"{setting_name} must be an absolute HTTP(S) URL")

        if not self.allowed_host_list:
            raise ValueError("At least one allowed host is required")

        # Toda la informacion del producto vive en PostgreSQL, en cualquier ambiente.
        if not self.database_url.startswith(("postgresql://", "postgresql+")):
            raise ValueError("DATABASE_URL must point to PostgreSQL")

        if not self.is_production:
            return self

        unsafe_reasons = []
        if self.app_debug:
            unsafe_reasons.append("APP_DEBUG must be false")
        if self.docs_enabled:
            unsafe_reasons.append("DOCS_ENABLED must be false")
        if not self.security_hsts_enabled:
            unsafe_reasons.append("SECURITY_HSTS_ENABLED must be true")
        if self.self_registration_enabled:
            unsafe_reasons.append("SELF_REGISTRATION_ENABLED must be false")
        if not self.session_cookie_secure:
            unsafe_reasons.append("SESSION_COOKIE_SECURE must be true")
        for setting_name, application_url in application_urls.items():
            if application_url and not application_url.startswith("https://"):
                unsafe_reasons.append(f"{setting_name} must use HTTPS")
        for image_origin in self.announcement_image_origin_list:
            if not image_origin.startswith("https://"):
                unsafe_reasons.append("ANNOUNCEMENT_IMAGE_ORIGINS must use HTTPS")
        if len(self.secret_key) < 32 or self.secret_key.lower().startswith("replace_"):
            unsafe_reasons.append(
                "SECRET_KEY must be a non-default 32+ character value"
            )
        unsafe_markers = ("change_me", "replace_", "local_development_only")
        password_is_unsafe = any(
            marker in self.postgres_password.lower() for marker in unsafe_markers
        )
        url_is_unsafe = any(
            marker in self.database_url.lower() for marker in unsafe_markers
        )
        if password_is_unsafe or url_is_unsafe:
            unsafe_reasons.append("PostgreSQL credentials must not use defaults")

        if unsafe_reasons:
            raise ValueError(
                "Unsafe production configuration: " + "; ".join(unsafe_reasons)
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

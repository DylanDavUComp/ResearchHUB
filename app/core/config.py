from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ResarchHUB"
    app_version: str = "0.1.0"
    app_env: str = "local"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    service_name: str = "researchhub-u"
    research_os_url: str | None = None
    cris_url: str | None = None
    crai_url: str | None = "https://crai.ucompensar.edu.co/"
    research_blog_url: str | None = None

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

    secret_key: str = "replace_with_secure_value_at_least_32_chars"
    access_token_expire_minutes: int = 30
    jwt_issuer: str = "researchhub-u"
    jwt_audience: str = "researchhub-u-web"
    log_level: str = "INFO"
    docs_enabled: bool = True
    self_registration_enabled: bool = False
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    cors_origins: str = ""
    security_hsts_enabled: bool = False
    bootstrap_superadmin_enabled: bool = False
    bootstrap_superadmin_name: str | None = None
    bootstrap_superadmin_email: str | None = None
    bootstrap_superadmin_password: str | None = None

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

    @model_validator(mode="after")
    def validate_operational_safety(self) -> "Settings":
        application_urls = {
            "RESEARCH_OS_URL": self.research_os_url,
            "CRIS_URL": self.cris_url,
            "CRAI_URL": self.crai_url,
            "RESEARCH_BLOG_URL": self.research_blog_url,
        }
        for setting_name, application_url in application_urls.items():
            if not application_url:
                continue
            parsed_url = urlsplit(application_url)
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
                raise ValueError(f"{setting_name} must be an absolute HTTP(S) URL")

        if self.bootstrap_superadmin_enabled:
            if not all(
                (
                    self.bootstrap_superadmin_name,
                    self.bootstrap_superadmin_email,
                    self.bootstrap_superadmin_password,
                )
            ):
                raise ValueError("Bootstrap credentials must be complete")
            if len(self.bootstrap_superadmin_password or "") < 16:
                raise ValueError(
                    "Bootstrap password must contain at least 16 characters"
                )

        if not self.allowed_host_list:
            raise ValueError("At least one allowed host is required")

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
        for setting_name, application_url in application_urls.items():
            if application_url and not application_url.startswith("https://"):
                unsafe_reasons.append(f"{setting_name} must use HTTPS")
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

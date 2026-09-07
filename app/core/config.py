from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ResearchHub-U"
    app_version: str = "0.1.0"
    app_env: str = "local"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    service_name: str = "researchhub-u"

    postgres_db: str = "researchhub_u"
    postgres_user: str = "researchhub_user"
    postgres_password: str = "change_me"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str = Field(
        default="postgresql+pg8000://researchhub_user:change_me@localhost:5432/researchhub_u"
    )

    secret_key: str = "replace_with_secure_value"
    access_token_expire_minutes: int = 30
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

"""Application settings, loaded from environment variables / .env."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration sourced from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Expense Receipt Processor"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    sql_echo: bool = False

    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    cors_allowed_headers: list[str] = Field(
        default_factory=lambda: ["Authorization", "Content-Type"]
    )
    cors_allowed_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PATCH", "DELETE"]
    )

    jwt_secret_key: str = "change-me-in-development-only"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    max_upload_size_bytes: int = 10 * 1024 * 1024
    allowed_upload_mime_types: list[str] = Field(
        default_factory=lambda: ["image/jpeg", "image/png", "application/pdf"]
    )
    upload_dir: str = "./data/uploads"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    extractor_provider: str = "anthropic"

    @property
    def database_url_sync(self) -> str:
        """Return a sync-driver variant of database_url, for Alembic migrations."""
        return self.database_url.replace("+aiosqlite", "")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance, loaded once per process."""
    return Settings()

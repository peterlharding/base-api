#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Application settings, loaded from the environment / .env at the repo root."""
# -----------------------------------------------------------------------------


from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


# -----------------------------------------------------------------------------
# app/core/config.py -> app/core -> app -> repo root

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


# -----------------------------------------------------------------------------

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application identity (APP_NAME, APP_TITLE in .env).
    # Prefixed on purpose: bare NAME/TITLE collide with common shell env vars.
    app_name: str = "base_api"
    app_title: str = "base-api"

    # Where the API listens (the Makefile uses these to launch uvicorn)
    host: str = "127.0.0.1"
    api_port: int = 8091

    # Postgres connection (see docker/db/SETUP.md)
    db_user: str = "api"
    db_password: str = ""
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "base_api"

    @property
    def database_url(self) -> str:
        """SQLAlchemy URL for the base_api database, connecting as `api`."""
        return (
            f"postgresql+psycopg://{quote_plus(self.db_user)}:"
            f"{quote_plus(self.db_password)}@{self.db_host}:{self.db_port}/{self.db_name}"
        )


# -----------------------------------------------------------------------------

@lru_cache
def get_settings() -> Settings:
    return Settings()


# -----------------------------------------------------------------------------


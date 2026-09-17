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

# The literal default for jwt_secret.  Named so handler.py can reject exactly
# this value without the two files drifting apart.
JWT_SECRET_PLACEHOLDER = "<This is replaced bythe value in .env at runtime>"


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

    # Postgres connection (see setup/SETUP.md)
    db_user: str = "api"
    db_password: str = ""
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "base_api"

    # Which deployment this is.  instance_metadata constrains the column to
    # these four values, and migration 0006 stamps the row from here: a
    # migration cannot otherwise know whether it is running against dev or
    # production.
    release: str = "dev"

    # Token signing.  The default is a placeholder, not a usable secret -
    # app/auth/handler.py rejects it by name, because a default that merely
    # looks wrong would still sign perfectly valid tokens on any deployment
    # missing a .env, using a string that is in the repository.
    jwt_algorithm: str = "HS256"
    jwt_secret: str = JWT_SECRET_PLACEHOLDER

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


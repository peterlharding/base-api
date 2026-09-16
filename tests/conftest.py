#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Fixtures shared by the test suite (see doc/TESTING.md).

The tests run against a dedicated Postgres (docker/test/docker-compose.yml),
never the dev database.  The env vars below are set *before* the app is
imported because app/db/session.py builds its engine at import time from
Settings; pydantic-settings prefers real environment variables over .env, so
the whole stack - app, SessionLocal and alembic (same get_settings()) - is
retargeted at the test database with no app changes and no dependency
overrides.

The connection details come from the TEST_* keys of the repo-root .env, the
same file docker/test/docker-compose.yml reads for TEST_DB_PORT, so `pytest`
and `make test` cannot disagree about the port.  The TEST_ prefix is what
keeps the suite safe: it never reads DB_PORT / DB_NAME / DB_PASSWORD, so
pointing those at the dev database cannot redirect the tests.

_TestDb is a separate Settings class on purpose - calling the app's own
get_settings() here would populate its lru_cache with the *dev* settings
before app.db.session ever builds its engine.
"""
# -----------------------------------------------------------------------------

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[1]


# --- pin the test database before any app import ------------------------------

class _TestDb(BaseSettings):
    """Test-database connection, from the TEST_* keys of the repo-root .env.

    The defaults match docker/test/docker-compose.yml, so the suite works on
    a checkout with no .env at all.
    """

    model_config = SettingsConfigDict(
        env_file=_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="TEST_",
        extra="ignore",
    )

    db_host:     str = "127.0.0.1"
    db_port:     int = 5433
    db_name:     str = "base_api_test"
    db_password: str = "test"


_test_db = _TestDb()

os.environ["DB_HOST"]     = _test_db.db_host
os.environ["DB_PORT"]     = str(_test_db.db_port)
os.environ["DB_NAME"]     = _test_db.db_name
os.environ["DB_PASSWORD"] = _test_db.db_password


# ------------------------------------------------------------------------------

import pytest
from alembic.command import upgrade
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text


# -----------------------------------------------------------------------------

from app.models.base import Base
from app.models import ApplicationUser  # noqa: F401  (register models on Base.metadata)
from app.db.session import SessionLocal
from app.main import app


# -----------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    """Bring the test schema to `head` once per run, using the real migrations.

    No-op when the database is already at head; runs the full chain on a
    freshly-reset container.  db/alembic.ini resolves script_location with
    %(here)s, so it works whatever directory pytest was started from.
    """
    cfg = Config(str(_ROOT / "db" / "alembic.ini"))
    upgrade(cfg, "head")


# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_tables() -> None:
    """Wipe every app table before each test.

    RESTART IDENTITY keeps primary keys predictable (1, 2, 3, ...) so tests
    can assert on them.  The table list comes from the model metadata, so
    new tables are covered automatically.  (The endpoints call db.commit(),
    so the transaction-rollback isolation pattern is not usable.)

    Deliberately *before* rather than after: truncating on the way out leaves
    the first test of a run exposed to whatever the container already held -
    a stray row from a manual session is enough to fail it, and the failure
    points at the wrong test.  Cleaning on the way in makes each test
    independent of everything that came before, inside the run or outside it.
    The last test's rows survive the run, which is useful for a post-mortem.
    """
    tables = ", ".join(f'"{name}"' for name in Base.metadata.tables)
    with SessionLocal() as session:
        session.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        session.commit()
    yield


# -----------------------------------------------------------------------------

@pytest.fixture()
def client() -> TestClient:
    """A TestClient on the real app — and therefore the test database."""
    return TestClient(app)


# -----------------------------------------------------------------------------

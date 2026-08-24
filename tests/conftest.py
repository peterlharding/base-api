#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Fixtures shared by the test suite (see doc/TESTING.md).

The tests run against a dedicated Postgres (docker/test/docker-compose.yml),
never the dev database.  The env vars below are set *before* the app is
imported because app/db/session.py builds its engine at import time from
Settings; pydantic-settings prefers real environment variables over .env, so
the whole stack — app, SessionLocal and alembic (same get_settings()) — is
retargeted at the test database with no app changes and no dependency
overrides.
"""
# -----------------------------------------------------------------------------

import os

# --- pin the test database before any app import ------------------------------
os.environ["DB_HOST"] = "127.0.0.1"
os.environ["DB_PORT"] = "5433"
os.environ["DB_NAME"] = "base_api_test"
os.environ["DB_PASSWORD"] = "test"  # matches docker/test/docker-compose.yml
# ------------------------------------------------------------------------------

from pathlib import Path

import pytest
from alembic.command import upgrade
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.base import Base
from app.db.models import ApplicationUser  # noqa: F401  (register models on Base.metadata)
from app.db.session import SessionLocal
from app.main import app


# -----------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parents[1]


# -----------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    """Bring the test schema to `head` once per run, using the real migrations.

    No-op when the database is already at head; runs the full chain on a
    freshly-reset container.  script_location is pinned to an absolute path
    because db/alembic.ini resolves it relative to the invocation directory.
    """
    cfg = Config(str(_ROOT / "db" / "alembic.ini"))
    cfg.set_main_option("script_location", str(_ROOT / "db" / "alembic"))
    upgrade(cfg, "head")


# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_tables() -> None:
    """Wipe every app table after each test.

    RESTART IDENTITY keeps primary keys predictable (1, 2, 3, ...) so tests
    can assert on them.  The table list comes from the model metadata, so
    new tables are covered automatically.  (The endpoints call db.commit(),
    so the transaction-rollback isolation pattern is not usable.)
    """
    yield
    tables = ", ".join(f'"{name}"' for name in Base.metadata.tables)
    with SessionLocal() as session:
        session.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        session.commit()


# -----------------------------------------------------------------------------

@pytest.fixture()
def client() -> TestClient:
    """A TestClient on the real app — and therefore the test database."""
    return TestClient(app)


# -----------------------------------------------------------------------------

#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Fixtures for exercising migrations against data.

Every other test in this suite runs against a database already at head, so a
migration that corrupts existing rows passes all of them.  That is not
hypothetical: migration 0004 silently cleared valid self-referencing values
and 222 tests stayed green.

These run against a scratch database of their own, created and dropped per
session, so moving its revision around cannot disturb the database the rest
of the suite shares.
"""
# -----------------------------------------------------------------------------

import pytest

from alembic.command import downgrade, upgrade
from alembic.config import Config
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


# -----------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parents[1]

SCRATCH_DB = "base_api_migration_test"


# -----------------------------------------------------------------------------

def _admin_url(settings) -> str:
    """A URL for the maintenance database, to CREATE and DROP from."""
    return (
        f"postgresql+psycopg://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/postgres"
    )


def _scratch_url(settings) -> str:
    return (
        f"postgresql+psycopg://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{SCRATCH_DB}"
    )


# -----------------------------------------------------------------------------

@pytest.fixture(scope="session")
def scratch_url():
    """Create a throwaway database for the session, and drop it afterwards.

    CREATE DATABASE cannot run inside a transaction, hence AUTOCOMMIT.
    """
    from app.core.config import get_settings

    settings = get_settings()
    admin = create_engine(_admin_url(settings), isolation_level="AUTOCOMMIT")

    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{SCRATCH_DB}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{SCRATCH_DB}"'))

    yield _scratch_url(settings)

    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{SCRATCH_DB}" WITH (FORCE)'))
    admin.dispose()


# -----------------------------------------------------------------------------

@pytest.fixture()
def migrate(scratch_url):
    """Move the scratch database to a revision, and hand back a session maker.

    Each test starts from an empty database: alembic is taken to base first,
    so one test's schema cannot leak into the next.
    """
    engine = create_engine(scratch_url)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    cfg = Config(str(_ROOT / "db" / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", scratch_url)

    def _to(revision: str) -> None:
        """Move to a revision in whichever direction is needed."""
        current = _current()
        if revision == "base":
            downgrade(cfg, "base")
        elif current is not None and revision != "head" and revision < current:
            downgrade(cfg, revision)
        else:
            upgrade(cfg, revision)

    def _current() -> str | None:
        with engine.connect() as c:
            if not c.exec_driver_sql(
                    "SELECT to_regclass('alembic_version') IS NOT NULL").scalar():
                return None
            return c.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()

    _to("base")

    class Helper:
        session = Session
        to = staticmethod(_to)

        @staticmethod
        def revision() -> str | None:
            with engine.connect() as c:
                return c.exec_driver_sql(
                    "SELECT version_num FROM alembic_version"
                ).scalar() if _has_alembic_table(c) else None

    def _has_alembic_table(conn) -> bool:
        return bool(conn.exec_driver_sql(
            "SELECT to_regclass('alembic_version') IS NOT NULL"
        ).scalar())

    yield Helper

    downgrade(cfg, "base")
    engine.dispose()


# -----------------------------------------------------------------------------

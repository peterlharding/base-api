"""/api/v1/instance-metadata - the singleton the front end reads for versions."""

import re

from sqlalchemy import delete, select

from app.core.version import app_version
from app.db.session import SessionLocal
from app.models import instance_metadata


# -----------------------------------------------------------------------------

def test_returns_an_object_not_a_list(client) -> None:
    """A singleton, so there is no list form and no path parameter."""
    r = client.get("/api/v1/instance-metadata")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


# -----------------------------------------------------------------------------

def test_reports_the_running_app_version(client) -> None:
    """app_version comes from pyproject, not the row.

    A value stamped into the row goes stale the moment the application is
    upgraded without a migration.
    """
    body = client.get("/api/v1/instance-metadata").json()
    assert body["app_version"] == app_version()
    assert re.fullmatch(r"v\d+\.\d+\.\d+", body["app_version"])


# -----------------------------------------------------------------------------

def test_reports_the_live_alembic_revision(client) -> None:
    body = client.get("/api/v1/instance-metadata").json()
    with SessionLocal() as s:
        from sqlalchemy import text
        current = s.scalar(text("SELECT version_num FROM alembic_version"))
    assert body["alembic_revision"] == current


# -----------------------------------------------------------------------------

def test_reports_release_and_db_version_from_the_row(client) -> None:
    body = client.get("/api/v1/instance-metadata").json()
    assert body["release"] in ("dev", "test", "staging", "prod")
    assert re.fullmatch(r"v\d+\.\d+\.\d+", body["db_version"])


# -----------------------------------------------------------------------------

def test_404_when_the_row_is_missing(client) -> None:
    """Rather than a 500 or an empty object, so the cause is legible.

    The row is put back afterwards.  It is stamped by migration 0006 and
    deliberately excluded from the per-test truncate, so nothing else would
    restore it and every later test - in this run or the next - would see an
    empty singleton.
    """
    with SessionLocal() as s:
        saved = dict(s.execute(select(instance_metadata)).mappings().one())
        s.execute(delete(instance_metadata))
        s.commit()

    try:
        r = client.get("/api/v1/instance-metadata")
        assert r.status_code == 404
        assert "0006" in r.json()["detail"]

    finally:
        with SessionLocal() as s:
            s.execute(instance_metadata.insert().values(**saved))
            s.commit()

    assert client.get("/api/v1/instance-metadata").status_code == 200


# -----------------------------------------------------------------------------

def test_is_not_writable(client) -> None:
    """Read-only: the row is the database's own description of itself."""
    for method in ("post", "put", "delete", "patch"):
        r = getattr(client, method)("/api/v1/instance-metadata")
        assert r.status_code == 405, f"{method.upper()} is accepted"

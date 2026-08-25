#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""SQLAlchemy table for instance_metadata (Core, not ORM-mapped)."""
# -----------------------------------------------------------------------------

from sqlalchemy import CheckConstraint, Column, DateTime, Table, Text, text


# -----------------------------------------------------------------------------

from app.db.base import Base


# -----------------------------------------------------------------------------

# A singleton table with no primary key — the ORM cannot map such a table,
# so it is a plain Table on Base.metadata (still visible to alembic
# autogenerate and the test suite).  The unique index on (true) and the
# set_when_modified trigger live in the migration.
#
# Query with:  session.execute(select(instance_metadata))
instance_metadata = Table(
    "instance_metadata",
    Base.metadata,
    Column("release", Text, nullable=False),
    Column("app_version", Text, nullable=False),
    Column("db_version", Text, nullable=False),
    Column("notes", Text, server_default=text("''"), nullable=False),
    Column(
        "when_modified",
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    ),
    CheckConstraint(
        "release IN ('dev', 'test', 'staging', 'prod')",
        name="instance_metadata_release_check",
    ),
    CheckConstraint(
        r"app_version ~ '^v\d+\.\d+\.\d+$'",
        name="instance_metadata_app_version_check",
    ),
    CheckConstraint(
        r"db_version ~ '^v\d+\.\d+\.\d+$'",
        name="instance_metadata_db_version_check",
    ),
)


# -----------------------------------------------------------------------------

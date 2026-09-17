#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  Stamp the instance_metadata singleton

  The table has existed since 0002 with release and version check
  constraints and a unique index on (true), but no row, so a GET against it
  returned nothing at all.

  release comes from Settings rather than a literal: a migration cannot know
  whether it is running against dev or production, and the check constraint
  only accepts dev, test, staging or prod.

  db_version is the release in which the schema last changed, not the running
  application version.  The endpoint reports app_version from pyproject.toml
  and alembic_revision from alembic_version at request time, because a
  version stamped into a row goes stale the moment the application is
  upgraded without a migration - which is most upgrades.  Any later migration
  that alters the schema should update this value.

  Idempotent: the unique index permits exactly one row, so this does nothing
  if a row is already there.
"""
# -----------------------------------------------------------------------------

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


# -----------------------------------------------------------------------------

revision:      str = '0006'
down_revision: str = '0005'

branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


# -----------------------------------------------------------------------------
# The release in which the schema last changed (migration 0005, the foreign
# key indexes).

DB_VERSION = "v0.7.1"


# -----------------------------------------------------------------------------

def upgrade() -> None:
    from app.core.config import get_settings

    release = get_settings().release

    op.execute(
        sa.text(
            "INSERT INTO instance_metadata (release, app_version, db_version, notes)"
            " SELECT :release, :db_version, :db_version,"
            "        'stamped by migration 0006'"
            " WHERE NOT EXISTS (SELECT 1 FROM instance_metadata)"
        ).bindparams(release=release, db_version=DB_VERSION)
    )


# -----------------------------------------------------------------------------

def downgrade() -> None:
    op.execute("DELETE FROM instance_metadata")


# -----------------------------------------------------------------------------

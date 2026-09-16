#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  Install the set_updated_at trigger function and the application_user table

  application_user comes first: token_blacklist and login_session both
  carry a foreign key to application_user(id), so it has to exist before
  0002 and 0003 run.
"""
# -----------------------------------------------------------------------------

from alembic import op
from pathlib import Path
from typing import Sequence, Union


# -----------------------------------------------------------------------------

revision:      str = '0001'
down_revision: Union[str, None] = None

branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


# -----------------------------------------------------------------------------
# Resolved from this file, not the current working directory, so alembic can
# be invoked from anywhere.  versions -> alembic -> db, then db/schema.
# -----------------------------------------------------------------------------

_SCHEMA = Path(__file__).resolve().parents[2] / "schema"


# -----------------------------------------------------------------------------

def _sql(*parts: str) -> str:
    """Return the contents of a script under db/schema/."""
    return _SCHEMA.joinpath(*parts).read_text()


# -----------------------------------------------------------------------------

def upgrade() -> None:
    op.execute(_sql("ddl", "set_updated_at.sql"))
    op.execute(_sql("create", "application_user.sql"))


# -----------------------------------------------------------------------------

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS application_user")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")


# -----------------------------------------------------------------------------

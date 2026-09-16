#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  Install the API tables: api_credentials, token_blacklist,
  instance_metadata, audit_log and login_session
"""
# -----------------------------------------------------------------------------

from alembic import op
from pathlib import Path
from typing import Sequence, Union


# -----------------------------------------------------------------------------

revision:      str = '0002'
down_revision: str = '0001'

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
    op.execute(_sql("create", "api_credentials.sql"))
    op.execute(_sql("create", "token_blacklist.sql"))
    op.execute(_sql("create", "instance_metadata.sql"))
    op.execute(_sql("create", "audit_log.sql"))
    op.execute(_sql("create", "login_session.sql"))


# -----------------------------------------------------------------------------

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS token_blacklist")
    op.execute("DROP TABLE IF EXISTS api_credentials")
    op.execute("DROP VIEW IF EXISTS login_session_active")
    op.execute("DROP TABLE IF EXISTS login_session")
    op.execute("DROP TABLE IF EXISTS audit_log")
    op.execute("DROP TABLE IF EXISTS instance_metadata")


# -----------------------------------------------------------------------------

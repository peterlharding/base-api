#!/usr/bin/env python
# 
# -----------------------------------------------------------------------------
"""
  Install the 12 CRM tables

  No foreign keys between them, so load order is unconstrained.
"""
# -----------------------------------------------------------------------------

from alembic import op
from pathlib import Path
from typing import Sequence, Union


# -----------------------------------------------------------------------------

revision:      str = '0003'
down_revision: str = '0002'

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
    op.execute(_sql("create", "access.sql"))
    op.execute(_sql("create", "account.sql"))
    op.execute(_sql("create", "attachment.sql"))
    op.execute(_sql("create", "contact.sql"))
    op.execute(_sql("create", "document.sql"))
    op.execute(_sql("create", "event.sql"))
    op.execute(_sql("create", "lead.sql"))
    op.execute(_sql("create", "note.sql"))
    op.execute(_sql("create", "opportunity.sql"))
    op.execute(_sql("create", "quote.sql"))
    op.execute(_sql("create", "task.sql"))
    op.execute(_sql("create", "user_role.sql"))


# -----------------------------------------------------------------------------

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS access")
    op.execute("DROP TABLE IF EXISTS account")
    op.execute("DROP TABLE IF EXISTS attachment")
    op.execute("DROP TABLE IF EXISTS contact")
    op.execute("DROP TABLE IF EXISTS document")
    op.execute("DROP TABLE IF EXISTS event")
    op.execute("DROP TABLE IF EXISTS lead")
    op.execute("DROP TABLE IF EXISTS note")
    op.execute("DROP TABLE IF EXISTS opportunity")
    op.execute("DROP TABLE IF EXISTS quote")
    op.execute("DROP TABLE IF EXISTS task")
    op.execute("DROP TABLE IF EXISTS user_role")



# -----------------------------------------------------------------------------


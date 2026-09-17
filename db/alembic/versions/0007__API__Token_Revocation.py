#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  Add application_user.tokens_revoked_before

  Wholesale token revocation - POST /api/v1/auth/revoke-all.  Every token
  issued to the user before this instant is refused; NULL means none have
  been revoked, which is every row until somebody uses the endpoint.

  A cutoff rather than more blacklist rows, because token_blacklist is keyed
  on jti and nothing holds a list of a user's outstanding jtis to insert.
  login_session records a hash of the token rather than its id, and a token
  obtained from refresh creates no session row at all, so "revoke everything
  outstanding" is not a query anyone can write.  One timestamp compared
  against a claim the token already carries covers all of them.

  ADD COLUMN IF NOT EXISTS, because db/schema/create/application_user.sql
  declares the column too: a fresh database gets it from migration 0001 and
  arrives here with the work already done, while an existing one does not.
  The same duplication in a constraint would fail - Postgres has no
  ADD CONSTRAINT IF NOT EXISTS - which is why constraints live only in the
  migration that introduces them.  A column can be in both.
"""
# -----------------------------------------------------------------------------

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


# -----------------------------------------------------------------------------

revision:      str = '0007'
down_revision: str = '0006'

branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


# -----------------------------------------------------------------------------
# The release in which the schema last changed - this one.  instance_metadata
# reports it, and a migration that alters the schema without updating it
# leaves the endpoint claiming an older shape than the database has.

DB_VERSION = "v0.15.0"


# -----------------------------------------------------------------------------

def upgrade() -> None:
    op.execute(
        "ALTER TABLE public.application_user"
        " ADD COLUMN IF NOT EXISTS tokens_revoked_before timestamptz"
    )

    op.execute(
        sa.text("UPDATE instance_metadata SET db_version = :db_version")
        .bindparams(db_version=DB_VERSION)
    )


# -----------------------------------------------------------------------------

def downgrade() -> None:
    op.execute(
        "ALTER TABLE public.application_user"
        " DROP COLUMN IF EXISTS tokens_revoked_before"
    )

    op.execute(
        sa.text("UPDATE instance_metadata SET db_version = :db_version")
        .bindparams(db_version="v0.7.1")
    )


# -----------------------------------------------------------------------------

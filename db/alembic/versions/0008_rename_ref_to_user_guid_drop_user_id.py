"""Rename application_user.ref to user_guid; drop user_id

The column holds the client-side GUID, and the new name matches the
convention already used by api_credentials.user_guid. user_id was
supposed to hold that same GUID as free text, so it is redundant and
is dropped. Any values it still holds are discarded - check the column
before upgrading if legacy data may hold something other than a copy
of ref.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-26

"""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "application_user",
        "ref",
        new_column_name="user_guid",
    )
    op.drop_column("application_user", "user_id")


def downgrade() -> None:
    # The dropped user_id data cannot be restored; the column comes back
    # empty.
    op.add_column(
        "application_user",
        sa.Column("user_id", sa.String(length=64), nullable=True),
    )
    op.alter_column(
        "application_user",
        "user_guid",
        new_column_name="ref",
    )

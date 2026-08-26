"""Change application_user.ref from character varying(40) to uuid

The legacy column was free text; application code treats ref as a UUID.
Existing values are cast in place: NULL stays NULL, empty strings become
NULL, and anything that is not a valid UUID fails the cast. Clean the
column before upgrading if the legacy table holds other non-UUID values.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-26

"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "application_user",
        "ref",
        type_=sa.Uuid(),
        existing_type=sa.String(length=40),
        existing_nullable=True,
        postgresql_using="NULLIF(ref, '')::uuid",
    )


def downgrade() -> None:
    # uuid::text is the dashed 36-character form, which fits varchar(40).
    op.alter_column(
        "application_user",
        "ref",
        type_=sa.String(length=40),
        existing_type=sa.Uuid(),
        existing_nullable=True,
        postgresql_using="ref::text",
    )

"""Create instance_metadata table

Mirrors db/schema/create/instance_metadata.sql. The trigger uses the
set_when_modified() function created in 0002.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-25

"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instance_metadata",
        sa.Column("release", sa.Text(), nullable=False),
        sa.Column("app_version", sa.Text(), nullable=False),
        sa.Column("db_version", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column(
            "when_modified",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "release IN ('dev', 'test', 'staging', 'prod')",
            name="instance_metadata_release_check",
        ),
        sa.CheckConstraint(
            r"app_version ~ '^v\d+\.\d+\.\d+$'",
            name="instance_metadata_app_version_check",
        ),
        sa.CheckConstraint(
            r"db_version ~ '^v\d+\.\d+\.\d+$'",
            name="instance_metadata_db_version_check",
        ),
    )
    # Singleton: a unique index on the constant expression (true) limits
    # the table to a single row.
    op.execute(
        "CREATE UNIQUE INDEX instance_metadata_singleton "
        "ON public.instance_metadata ((true))"
    )
    op.execute(
        """
        CREATE TRIGGER instance_metadata_set_when_modified
            BEFORE UPDATE ON public.instance_metadata
            FOR EACH ROW
            WHEN (OLD.* IS DISTINCT FROM NEW.*)
            EXECUTE FUNCTION public.set_when_modified()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER instance_metadata_set_when_modified ON public.instance_metadata")
    op.drop_table("instance_metadata")

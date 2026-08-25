"""Create set_when_modified trigger function and application_user trigger

Mirrors db/schema/ddl/set_when_modified.sql, plus the when_modified column on
application_user that the trigger maintains (the legacy table pre-dates it).

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-25

"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "application_user",
        sa.Column(
            "when_modified",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.execute(
        """
        CREATE FUNCTION public.set_when_modified()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.when_modified := now();
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER application_user_set_when_modified
            BEFORE UPDATE ON public.application_user
            FOR EACH ROW
            WHEN (OLD.* IS DISTINCT FROM NEW.*)
            EXECUTE FUNCTION public.set_when_modified()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER application_user_set_when_modified ON public.application_user")
    op.execute("DROP FUNCTION public.set_when_modified()")
    op.drop_column("application_user", "when_modified")

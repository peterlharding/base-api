"""Create login_session table and login_session_active view

Mirrors db/schema/create/login_session.sql.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-25

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "login_session",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("session_token_hash", postgresql.BYTEA, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("application_user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("workstation", sa.Text()),
        sa.Column("ip_address", postgresql.INET),
        sa.Column("user_agent", sa.Text()),
        sa.Column(
            "data",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "started",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now() + interval '12 hours'"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("session_token_hash", name="login_session_token_key"),
        sa.CheckConstraint("expires_at > started", name="login_session_expiry_check"),
        sa.CheckConstraint("jsonb_typeof(data) = 'object'", name="login_session_data_object"),
    )
    op.create_index("login_session_user_id_idx", "login_session", ["user_id"])
    op.create_index("login_session_expires_at_idx", "login_session", ["expires_at"])
    op.execute(
        """
        CREATE VIEW public.login_session_active AS
            SELECT * FROM public.login_session
            WHERE revoked_at IS NULL
              AND expires_at > now()
        """
    )


def downgrade() -> None:
    # The view depends on the table, so it must go first.
    op.execute("DROP VIEW public.login_session_active")
    op.drop_table("login_session")

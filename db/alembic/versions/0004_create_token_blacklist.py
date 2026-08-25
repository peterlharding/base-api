"""Create token_blacklist table

Mirrors db/schema/create/token_blacklist.sql.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-25

"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "token_blacklist",
        sa.Column("jti", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("application_user.id", ondelete="CASCADE"),
        ),
        sa.Column("reason", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("expiry", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "blacklisted_on",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("token_blacklist_expiry_idx", "token_blacklist", ["expiry"])
    op.create_index("token_blacklist_user_id_idx", "token_blacklist", ["user_id"])
    op.execute(
        "COMMENT ON TABLE public.token_blacklist IS "
        "'Revoked token IDs. Rows are deletable once expiry passes — "
        "the token fails validation anyway.'"
    )


def downgrade() -> None:
    op.drop_table("token_blacklist")

"""create application_user table

Mirrors db/schema/create/03-create-application_user.sql so a fresh database can be
built with `alembic upgrade head` instead of the psql scripts.

Revision ID: 0001
Revises:
Create Date: 2026-08-22

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # alembic has no create_sequence op; raw DDL keeps the migration
    # faithful to db/schema/create/03-create-application_user.sql.
    op.execute("CREATE SEQUENCE application_user_id_seq")
    op.create_table(
        "application_user",
        sa.Column(
            "id",
            sa.Integer(),
            server_default=sa.text("nextval('application_user_id_seq'::regclass)"),
            nullable=False,
        ),
        sa.Column("ref", sa.String(length=40), nullable=True),
        sa.Column("username", sa.String(length=32), nullable=True),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("password", sa.String(length=128), nullable=True),
        sa.Column("first_name", sa.String(length=32), nullable=True),
        sa.Column("last_name", sa.String(length=32), nullable=True),
        sa.Column("company_name", sa.String(length=32), nullable=True),
        sa.Column("division", sa.String(length=32), nullable=True),
        sa.Column("department", sa.String(length=40), nullable=True),
        sa.Column("title", sa.String(length=40), nullable=True),
        sa.Column("street", sa.String(length=40), nullable=True),
        sa.Column("city", sa.String(length=32), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=True),
        sa.Column("postal_code", sa.String(length=18), nullable=True),
        sa.Column("country", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=64), nullable=True),
        sa.Column("phone", sa.String(length=24), nullable=True),
        sa.Column("fax", sa.String(length=24), nullable=True),
        sa.Column("mobile_phone", sa.String(length=24), nullable=True),
        sa.Column("alias", sa.String(length=24), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column(
            "timezone_key",
            sa.String(length=32),
            server_default=sa.text("'Australia/Melbourne'"),
            nullable=True,
        ),
        sa.Column("user_role_id", sa.Integer(), nullable=True),
        sa.Column("locale_key", sa.String(length=12), server_default=sa.text("'en_AU'"), nullable=True),
        sa.Column(
            "email_encoding_key",
            sa.String(length=18),
            server_default=sa.text("'ISO-8859-1'"),
            nullable=True,
        ),
        sa.Column("profile_id", sa.Integer(), nullable=True),
        sa.Column("employee_number", sa.String(length=20), nullable=True),
        sa.Column("user_type", sa.String(length=20), server_default=sa.text("'Standard'"), nullable=True),
        sa.Column("start_day", sa.Integer(), server_default=sa.text("6"), nullable=True),
        sa.Column("end_day", sa.Integer(), server_default=sa.text("23"), nullable=True),
        sa.Column(
            "language_locale_key",
            sa.String(length=12),
            server_default=sa.text("'en_US'"),
            nullable=True,
        ),
        sa.Column("delegated_approver_id", sa.Integer(), nullable=True),
        sa.Column(
            "last_login_date",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "created_date",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "last_modified_date",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("last_modified_by_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # Same ownership as a SERIAL column, so dropping the table drops the sequence.
    op.execute("ALTER SEQUENCE application_user_id_seq OWNED BY public.application_user.id")


def downgrade() -> None:
    op.drop_table("application_user")

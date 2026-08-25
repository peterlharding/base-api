"""Create api_credentials table with seed rows

Mirrors db/schema/create/api_credentials.sql. The seed INSERT needs
OVERRIDING SYSTEM VALUE because id is GENERATED ALWAYS AS IDENTITY —
Postgres rejects a plain INSERT of explicit ids into such a column.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-25

"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_credentials",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "user_guid",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            unique=True,
        ),
        sa.Column("email", sa.String(length=128), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=128), nullable=False),
    )
    op.execute(
        """
        INSERT INTO public.api_credentials (id, user_guid, email, hashed_password)
            OVERRIDING SYSTEM VALUE
        VALUES
            (1, 'ff40bf6f-e202-4348-8a05-d84a9098d2d2', 'api@performiq.com',
                'c2030e133a44709fbd527524a80bd5e9774fed58690c6fe19f4abdea50b0cc98'),
            (2, 'bcc26c7e-3124-4023-a743-2ffa11a6731e', 'plh@performiq.com',
                'c2030e133a44709fbd527524a80bd5e9774fed58690c6fe19f4abdea50b0cc98'),
            (3, '148e1d8f-97f5-45b4-bfbc-d9da86f1c0ed', 'peterlharding@gmail.com',
                'c2030e133a44709fbd527524a80bd5e9774fed58690c6fe19f4abdea50b0cc98'),
            (4, '8bd2c76a-2018-41e1-bd97-87ae639a3aba', 'bgg@gobject-craft.com.au',
                'c2030e133a44709fbd527524a80bd5e9774fed58690c6fe19f4abdea50b0cc98')
        """
    )


def downgrade() -> None:
    op.drop_table("api_credentials")

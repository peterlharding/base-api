"""Declarative base shared by all models (and alembic autogenerate).

Lives beside the models so there is exactly one Base: a second
DeclarativeBase would give a second metadata, and models would split
across the two invisibly.
"""

from sqlalchemy.orm import DeclarativeBase


# -----------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# -----------------------------------------------------------------------------


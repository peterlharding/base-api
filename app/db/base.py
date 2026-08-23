"""Declarative base shared by all models (and alembic autogenerate)."""

from sqlalchemy.orm import DeclarativeBase


# -----------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# -----------------------------------------------------------------------------


#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""SQLAlchemy model for the api_credentials table."""
# -----------------------------------------------------------------------------

from uuid import UUID

from sqlalchemy import Identity, Integer, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column


# -----------------------------------------------------------------------------

from app.db.base import Base


# -----------------------------------------------------------------------------

class ApiCredential(Base):
    """Mirrors the api_credentials table (see db/schema/create/api_credentials.sql)."""

    __tablename__ = "api_credentials"

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)

    user_guid: Mapped[UUID] = mapped_column(
        Uuid, server_default=text("gen_random_uuid()"), nullable=False, unique=True
    )
    email: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)


# -----------------------------------------------------------------------------

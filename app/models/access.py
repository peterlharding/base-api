#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  access - db/schema/create/access.sql
"""
# -----------------------------------------------------------------------------

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column


# -----------------------------------------------------------------------------

from app.models.base import Base


# -----------------------------------------------------------------------------

class Access(Base):
    __tablename__ = "access"
    __table_args__ = (
        # one per foreign key: Postgres indexes the parent side only,
        # so without these a parent delete scans this table
        Index("access_owner_id_idx", "owner_id"),
        Index("access_user_id_idx", "user_id"),
    )

    id:                   Mapped[int]        = mapped_column(BigInteger, Identity(always=True), primary_key=True)

    access_type:          Mapped[str | None] = mapped_column(String(20))
    reference_name:       Mapped[str | None] = mapped_column(String(255))
    reference_type:       Mapped[str | None] = mapped_column(String(32))

    reference_id:         Mapped[int | None] = mapped_column(BigInteger)
    owner_id:             Mapped[int | None] = mapped_column(BigInteger, ForeignKey("application_user.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    user_id:              Mapped[int | None] = mapped_column(BigInteger, ForeignKey("application_user.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    last_referenced_date: Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())


# -----------------------------------------------------------------------------

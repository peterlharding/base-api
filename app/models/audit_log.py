#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  audit_log - db/schema/create/audit_log.sql
"""
# -----------------------------------------------------------------------------

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column


# -----------------------------------------------------------------------------

from app.models.base import Base


# -----------------------------------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_log"

    id:             Mapped[int]        = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    application:    Mapped[str]        = mapped_column(String(32))
    reference_type: Mapped[int]        = mapped_column(Integer)
    reference_id:   Mapped[int]        = mapped_column(Integer)
    reference:      Mapped[str | None] = mapped_column(String(50))
    event:          Mapped[str]        = mapped_column(String(50))
    description:    Mapped[str]        = mapped_column(String(256))
    user_id:        Mapped[str]        = mapped_column(String(50))
    created_at:     Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())


# -----------------------------------------------------------------------------

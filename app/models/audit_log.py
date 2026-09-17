#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  audit_log - db/schema/create/audit_log.sql

  Append-only, and written only by app/api/v1/crud.py.  There is no update or
  delete path: an audit trail the recorded parties can edit is not one.
"""
# -----------------------------------------------------------------------------

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column


# -----------------------------------------------------------------------------

from app.models.base import Base


# -----------------------------------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        # what happened to this row, and what has this user been doing
        Index("audit_log_reference_idx", "reference_type", "reference_id"),
        Index("audit_log_user_id_idx", "user_id"),
        Index("audit_log_created_at_idx", text("created_at DESC")),
    )

    id:             Mapped[int]        = mapped_column(BigInteger, Identity(always=True), primary_key=True)

    application:    Mapped[str]        = mapped_column(String(32))
    action:         Mapped[str]        = mapped_column(String(32))

    reference_type: Mapped[str]        = mapped_column(String(64))
    reference_id:   Mapped[int | None] = mapped_column(BigInteger)

    description:    Mapped[str]        = mapped_column(Text, server_default=text("''"))

    user_id:        Mapped[str]        = mapped_column(String(50))

    created_at:     Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())


# -----------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------

    @classmethod
    def prune_older_than(cls, session, days: int, *, now=None) -> int:
        """Delete audit entries older than ``days``.  Returns the count.

        ``days`` of 0 means keep indefinitely and deletes nothing, which is
        the default: an audit trail that deletes itself on a timer is a weaker
        guarantee than one that does not.  The method exists so that a
        deployment which must bound this table can, by setting
        AUDIT_LOG_RETENTION_DAYS rather than by writing code.

        Deleting from here is deliberately not itself audited.  An entry
        recording the removal of entries is of no use to anyone reading the
        table, and the pruning run reports what it did.
        """
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import delete

        if days <= 0:
            return 0

        cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)

        return session.execute(delete(cls).where(cls.created_at < cutoff)).rowcount


# -----------------------------------------------------------------------------

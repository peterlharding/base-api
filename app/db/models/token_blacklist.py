#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""SQLAlchemy model for the token_blacklist table."""
# -----------------------------------------------------------------------------

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column


# -----------------------------------------------------------------------------

from app.db.base import Base


# -----------------------------------------------------------------------------

class TokenBlacklist(Base):
    """Mirrors the token_blacklist table (see db/schema/create/token_blacklist.sql)."""

    __tablename__ = "token_blacklist"
    __table_args__ = (
        Index("token_blacklist_expiry_idx", "expiry"),
        Index("token_blacklist_user_id_idx", "user_id"),
        {
            "comment": (
                "Revoked token IDs. Rows are deletable once expiry passes — "
                "the token fails validation anyway."
            )
        },
    )

    jti: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("application_user.id", ondelete="CASCADE")
    )
    reason: Mapped[str] = mapped_column(Text, server_default=text("''"), nullable=False)
    expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    blacklisted_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )


# -----------------------------------------------------------------------------

#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""SQLAlchemy model for the token_blacklist table."""
# -----------------------------------------------------------------------------

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column


# -----------------------------------------------------------------------------

from app.models.base import Base


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

    jti:                Mapped[UUID] = mapped_column(Uuid, primary_key=True)

    user_id:            Mapped[int | None] = mapped_column(
                            BigInteger, ForeignKey("application_user.id", ondelete="CASCADE")
                        )

    reason:             Mapped[str] = mapped_column(Text, server_default=text("''"), nullable=False)
    expiry:             Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    blacklisted_on:     Mapped[datetime] = mapped_column(
                            DateTime(timezone=True), server_default=text("now()"), nullable=False
                        )


# -----------------------------------------------------------------------------

    # -------------------------------------------------------------------------

    @classmethod
    def check_blacklist(cls, session, jti: str) -> bool:
        """True if this token id has been revoked.

        Takes the caller's session rather than opening its own, so the check
        joins the surrounding request transaction.
        """
        from sqlalchemy import select

        return session.scalar(select(cls.jti).where(cls.jti == jti)) is not None


# -----------------------------------------------------------------------------

    # -------------------------------------------------------------------------

    @classmethod
    def prune_expired(cls, session, *, now=None) -> int:
        """Delete rows whose token has expired anyway.  Returns the count.

        A blacklist entry only has to outlive the token it revokes: once the
        expiry has passed, the token fails validation on its own and the row
        is answering a question nobody will ask.  Without this the table
        grows by one row per logout and never shrinks.

        Safe to call concurrently - it deletes only rows that are already
        past their expiry, so two callers racing simply delete the same
        already-dead rows.

        The expiry index makes this a range scan rather than a table scan.
        """
        from datetime import datetime, timezone

        from sqlalchemy import delete

        cutoff = now or datetime.now(timezone.utc)

        return session.execute(
            delete(cls).where(cls.expiry < cutoff)
        ).rowcount


# -----------------------------------------------------------------------------

#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""SQLAlchemy model for the application_user table.

Mirrors db/schema/create/application_user.sql, installed by migration 0001.
Server defaults are declared so `alembic revision --autogenerate` reports no
diff, and so a create returns the database's own values untouched.
"""
# -----------------------------------------------------------------------------

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.ext.hybrid import (
    hybrid_property,
    hybrid_method
)


# -----------------------------------------------------------------------------

from app.models.base import Base


# -----------------------------------------------------------------------------

class ApplicationUser(Base):
    """Mirrors the application_user table (see db/schema/create/application_user.sql)."""

    __tablename__ = "application_user"
    __table_args__ = (
        # one per foreign key: Postgres indexes the parent side only,
        # so without these a parent delete scans this table
        Index("application_user_delegated_approver_id_idx", "delegated_approver_id"),
        Index("application_user_user_role_id_idx", "user_role_id"),
    )

    id:                           Mapped[int]         = mapped_column(
        BigInteger, primary_key=True
    )

    guid:                         Mapped[UUID | None] = mapped_column(Uuid)

    username:                     Mapped[str | None]  = mapped_column(String(32))
    hashed_password:              Mapped[str | None]  = mapped_column(String(255))
    alias:                        Mapped[str | None]  = mapped_column(String(32))

    first_name:                   Mapped[str | None]  = mapped_column(String(32))
    last_name:                    Mapped[str | None]  = mapped_column(String(32))

    company_name:                 Mapped[str | None]  = mapped_column(String(100))
    division:                     Mapped[str | None]  = mapped_column(String(32))
    department:                   Mapped[str | None]  = mapped_column(String(100))
    title:                        Mapped[str | None]  = mapped_column(String(100))

    street:                       Mapped[str | None]  = mapped_column(String(100))
    city:                         Mapped[str | None]  = mapped_column(String(50))
    state:                        Mapped[str | None]  = mapped_column(String(32))
    postal_code:                  Mapped[str | None]  = mapped_column(String(20))
    country:                      Mapped[str | None]  = mapped_column(String(100))

    email:                        Mapped[str | None]  = mapped_column(String(255), unique=True)
    phone:                        Mapped[str | None]  = mapped_column(String(20))
    phone_extension:              Mapped[str | None]  = mapped_column(String(10))
    fax:                          Mapped[str | None]  = mapped_column(String(20))
    mobile_phone:                 Mapped[str | None]  = mapped_column(String(20))

    is_active:                    Mapped[bool | None] = mapped_column(
        Boolean, server_default=text("true")
    )

    user_role_id:                 Mapped[int | None]  = mapped_column(BigInteger, ForeignKey("user_role.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    user_type:                    Mapped[str | None]  = mapped_column(
        String(20), server_default=text("'Standard'")
    )

    profile_id:                   Mapped[int | None]  = mapped_column(BigInteger)

    timezone_sid_key:             Mapped[str | None]  = mapped_column(
        String(32), server_default=text("'Australia/Melbourne'")
    )

    locale_sid_key:               Mapped[str | None]  = mapped_column(
        String(32), server_default=text("'en_AU'")
    )

    language_locale_key:          Mapped[str | None]  = mapped_column(
        String(32), server_default=text("'en_US'")
    )

    receives_info_emails:         Mapped[bool | None] = mapped_column(
        Boolean, server_default=text("false")
    )

    receives_admin_info_emails:   Mapped[bool | None] = mapped_column(
        Boolean, server_default=text("false")
    )

    email_encoding_key:           Mapped[str | None]  = mapped_column(
        String(32), server_default=text("'ISO-8859-1'")
    )

    employee_number:              Mapped[str | None]  = mapped_column(String(50))
    delegated_approver_id:        Mapped[int | None]  = mapped_column(BigInteger, ForeignKey("application_user.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    start_day:                    Mapped[int | None]  = mapped_column(
        Integer, server_default=text("6")
    )

    end_day:                      Mapped[int | None]  = mapped_column(
        Integer, server_default=text("23")
    )

    last_login_date:              Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # created_at / updated_at are server-maintained: updated_at is advanced by
    # the application_user_set_updated_at trigger, never written by the app.
    created_at:                   Mapped[datetime]    = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    created_by_id:                Mapped[int | None]  = mapped_column(BigInteger)

    updated_at:                   Mapped[datetime]    = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    updated_by_id:                Mapped[int | None]  = mapped_column(BigInteger)

    hash                                = '0052'


    # -------------------------------------------------------------------------
    # Computed display names. NULL-safe Python implementations; no
    # `.expression` overrides yet because we only use these in
    # templates, not in WHERE clauses. Add a SQL expression if/when
    # we need to filter or order by them at the DB.

    @hybrid_property
    def first_last_name(self) -> str:
        """First Last - the natural human display."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @hybrid_property
    def last_first_name(self) -> str:
        """Last, First - the sortable display (related lists, headers)."""
        if self.first_name and self.last_name:
            return f"{self.last_name}, {self.first_name}"
        return self.last_name or self.first_name or ''

    # -------------------------------------------------------------------------

    def __str__(self):
        return '<User: %r <%s>>' % (self.id, self.guid)

    # -------------------------------------------------------------------------

    def __repr__(self):
        return f"""<User:
           id: {self.id}
         guid: {self.guid}
     username: {self.username}
   first_name: {self.first_name}
    last_name: {self.last_name}
 company_name: {self.company_name}
"""

    # -------------------------------------------------------------------------


# =============================================================================

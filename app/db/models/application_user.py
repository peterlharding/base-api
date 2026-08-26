#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""SQLAlchemy model for the application_user table."""
# -----------------------------------------------------------------------------

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.ext.hybrid import (
    hybrid_property,
    hybrid_method
)


# -----------------------------------------------------------------------------

from app.db.base import Base


# -----------------------------------------------------------------------------

class ApplicationUser(Base):
    """Mirrors the application_user table (see db/schema/create/03-create-application_user.sql)."""

    __tablename__ = "application_user"

    id:                           Mapped[int]        = mapped_column(
        Integer,
        primary_key=True,
        server_default=text("nextval('application_user_id_seq'::regclass)"),
    )

    ref:                          Mapped[UUID | None] = mapped_column(Uuid)
    username:                     Mapped[str | None]  = mapped_column(String(32))
    user_id:                      Mapped[str | None]  = mapped_column(String(64))
    password:                     Mapped[str | None]  = mapped_column(String(128))
    first_name:                   Mapped[str | None]  = mapped_column(String(32))
    last_name:                    Mapped[str | None]  = mapped_column(String(32))
    company_name:                 Mapped[str | None]  = mapped_column(String(32))
    division:                     Mapped[str | None]  = mapped_column(String(32))
    department:                   Mapped[str | None]  = mapped_column(String(40))
    title:                        Mapped[str | None]  = mapped_column(String(40))
    street:                       Mapped[str | None]  = mapped_column(String(40))
    city:                         Mapped[str | None]  = mapped_column(String(32))
    state:                        Mapped[str | None]  = mapped_column(String(32))
    postal_code:                  Mapped[str | None]  = mapped_column(String(18))
    country:                      Mapped[str | None]  = mapped_column(String(32))
    email:                        Mapped[str | None]  = mapped_column(String(64))
    phone:                        Mapped[str | None]  = mapped_column(String(24))
    fax:                          Mapped[str | None]  = mapped_column(String(24))
    mobile_phone:                 Mapped[str | None]  = mapped_column(String(24))
    alias:                        Mapped[str | None]  = mapped_column(String(24))
    is_active:                    Mapped[bool | None] = mapped_column(Boolean, server_default=text("true"))

    timezone_key:                 Mapped[str | None]  = mapped_column(
        String(32), server_default=text("'Australia/Melbourne'")
    )

    user_role_id:                 Mapped[int | None]  = mapped_column(Integer)
    locale_key:                   Mapped[str | None]  = mapped_column(String(12), server_default=text("'en_AU'"))

    email_encoding_key:           Mapped[str | None] = mapped_column(
        String(18), server_default=text("'ISO-8859-1'")
    )

    profile_id:                   Mapped[int | None]  = mapped_column(Integer)
    employee_number:              Mapped[str | None]  = mapped_column(String(20))
    user_type:                    Mapped[str | None]  = mapped_column(String(20), server_default=text("'Standard'"))
    start_day:                    Mapped[int | None]  = mapped_column(Integer, server_default=text("6"))
    end_day:                      Mapped[int | None]  = mapped_column(Integer, server_default=text("23"))

    language_locale_key:          Mapped[str | None]  = mapped_column(
        String(12), server_default=text("'en_US'")
    )

    delegated_approver_id:        Mapped[int | None]  = mapped_column(Integer)

    last_login_date:              Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    created_date:                 Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    created_by_id:                Mapped[int | None]  = mapped_column(Integer)

    last_modified_date:           Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    last_modified_by_id:          Mapped[int | None]  = mapped_column(Integer)

    # Added by migration 0002 (the legacy table pre-dates it); maintained by
    # the set_when_modified trigger, never written by the app.
    when_modified:                Mapped[datetime]    = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

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
        return '<User: %r <%s>>' % (self.id, self.ref)

    # -------------------------------------------------------------------------

    def __repr__(self):
        return f"""<User:
           id: {self.id}
          ref: {self.ref}
     username: {self.username}
   first_name: {self.first_name}
    last_name: {self.last_name}
 company_name: {self.company_name}
"""

    # -------------------------------------------------------------------------


# =============================================================================



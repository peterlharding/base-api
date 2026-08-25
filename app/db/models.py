#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""SQLAlchemy models for the base_api database."""
# -----------------------------------------------------------------------------

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column


# -----------------------------------------------------------------------------

from app.db.base import Base


# -----------------------------------------------------------------------------

class ApplicationUser(Base):
    """Mirrors the application_user table (see db/schema/create/03-create-application_user.sql)."""

    __tablename__ = "application_user"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        server_default=text("nextval('application_user_id_seq'::regclass)"),
    )

    ref: Mapped[str | None] = mapped_column(String(40))
    username: Mapped[str | None] = mapped_column(String(32))
    user_id: Mapped[str | None] = mapped_column(String(64))
    password: Mapped[str | None] = mapped_column(String(128))
    first_name: Mapped[str | None] = mapped_column(String(32))
    last_name: Mapped[str | None] = mapped_column(String(32))
    company_name: Mapped[str | None] = mapped_column(String(32))
    division: Mapped[str | None] = mapped_column(String(32))
    department: Mapped[str | None] = mapped_column(String(40))
    title: Mapped[str | None] = mapped_column(String(40))
    street: Mapped[str | None] = mapped_column(String(40))
    city: Mapped[str | None] = mapped_column(String(32))
    state: Mapped[str | None] = mapped_column(String(32))
    postal_code: Mapped[str | None] = mapped_column(String(18))
    country: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(64))
    phone: Mapped[str | None] = mapped_column(String(24))
    fax: Mapped[str | None] = mapped_column(String(24))
    mobile_phone: Mapped[str | None] = mapped_column(String(24))
    alias: Mapped[str | None] = mapped_column(String(24))
    is_active: Mapped[bool | None] = mapped_column(Boolean, server_default=text("true"))

    timezone_key: Mapped[str | None] = mapped_column(
        String(32), server_default=text("'Australia/Melbourne'")
    )

    user_role_id: Mapped[int | None] = mapped_column(Integer)
    locale_key: Mapped[str | None] = mapped_column(String(12), server_default=text("'en_AU'"))

    email_encoding_key: Mapped[str | None] = mapped_column(
        String(18), server_default=text("'ISO-8859-1'")
    )

    profile_id: Mapped[int | None] = mapped_column(Integer)
    employee_number: Mapped[str | None] = mapped_column(String(20))
    user_type: Mapped[str | None] = mapped_column(String(20), server_default=text("'Standard'"))
    start_day: Mapped[int | None] = mapped_column(Integer, server_default=text("6"))
    end_day: Mapped[int | None] = mapped_column(Integer, server_default=text("23"))

    language_locale_key: Mapped[str | None] = mapped_column(
        String(12), server_default=text("'en_US'")
    )

    delegated_approver_id: Mapped[int | None] = mapped_column(Integer)

    last_login_date: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    created_date: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    created_by_id: Mapped[int | None] = mapped_column(Integer)

    last_modified_date: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    last_modified_by_id: Mapped[int | None] = mapped_column(Integer)


# -----------------------------------------------------------------------------


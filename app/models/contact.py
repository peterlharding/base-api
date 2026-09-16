#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  contact - db/schema/create/contact.sql

  guid is an 18 character Salesforce-style id, not a uuid.
"""
# -----------------------------------------------------------------------------

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Identity, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column


# -----------------------------------------------------------------------------

from app.models.base import Base


# -----------------------------------------------------------------------------

class Contact(Base):
    __tablename__ = "contact"

    id:                     Mapped[int]         = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    guid:                   Mapped[str | None]  = mapped_column(String(18))

    salutation:             Mapped[str | None]  = mapped_column(String(24))
    first_name:             Mapped[str | None]  = mapped_column(String(32))
    last_name:              Mapped[str | None]  = mapped_column(String(64))

    title:                  Mapped[str | None]  = mapped_column(String(96))
    department:             Mapped[str | None]  = mapped_column(String(96))
    account_id:             Mapped[int | None]  = mapped_column(BigInteger)

    description:            Mapped[str | None]  = mapped_column(Text)
    notes:                  Mapped[str | None]  = mapped_column(Text)

    other_street:           Mapped[str | None]  = mapped_column(String(96))
    other_city:             Mapped[str | None]  = mapped_column(String(32))
    other_state:            Mapped[str | None]  = mapped_column(String(20))
    other_postal_code:      Mapped[str | None]  = mapped_column(String(18))
    other_country:          Mapped[str | None]  = mapped_column(String(18))

    mailing_street:         Mapped[str | None]  = mapped_column(String(96))
    mailing_city:           Mapped[str | None]  = mapped_column(String(32))
    mailing_state:          Mapped[str | None]  = mapped_column(String(20))
    mailing_postal_code:    Mapped[str | None]  = mapped_column(String(10))
    mailing_country:        Mapped[str | None]  = mapped_column(String(32))

    phone:                  Mapped[str | None]  = mapped_column(String(18))
    fax:                    Mapped[str | None]  = mapped_column(String(18))
    mobile_phone:           Mapped[str | None]  = mapped_column(String(18))
    home_phone:             Mapped[str | None]  = mapped_column(String(18))
    other_phone:            Mapped[str | None]  = mapped_column(String(18))
    email:                  Mapped[str | None]  = mapped_column(String(64))

    assistant_name:         Mapped[str | None]  = mapped_column(String(96))
    assistant_phone:        Mapped[str | None]  = mapped_column(String(18))

    reports_to_id:          Mapped[int | None]  = mapped_column(BigInteger)

    owner_id:               Mapped[int | None]  = mapped_column(BigInteger)

    lead_source:            Mapped[str | None]  = mapped_column(Text)

    birthdate:              Mapped[date | None] = mapped_column(Date)

    do_not_call:            Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    has_opted_out_of_email: Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    has_opted_out_of_fax:   Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))

    last_activity_date:     Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())

    is_deleted:             Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))

    created_at:             Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id:          Mapped[int | None]  = mapped_column(BigInteger)
    updated_at:             Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by_id:          Mapped[int | None]  = mapped_column(BigInteger)


# -----------------------------------------------------------------------------

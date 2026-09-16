#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  lead - db/schema/create/lead.sql
"""
# -----------------------------------------------------------------------------

import uuid

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# -----------------------------------------------------------------------------

class Lead(Base):
    __tablename__ = "lead"

    id:                       Mapped[int]              = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    guid:                     Mapped[uuid.UUID | None] = mapped_column(Uuid)

    description:              Mapped[str | None]       = mapped_column(Text)

    salutation:               Mapped[str | None]       = mapped_column(String(24))
    first_name:               Mapped[str | None]       = mapped_column(String(32))
    last_name:                Mapped[str | None]       = mapped_column(String(64))

    title:                    Mapped[str | None]       = mapped_column(String(128))
    company:                  Mapped[str | None]       = mapped_column(String(96))

    street:                   Mapped[str | None]       = mapped_column(Text)
    city:                     Mapped[str | None]       = mapped_column(String(64))
    state:                    Mapped[str | None]       = mapped_column(String(32))
    postal_code:              Mapped[str | None]       = mapped_column(String(18))
    country:                  Mapped[str | None]       = mapped_column(String(32))

    phone:                    Mapped[str | None]       = mapped_column(String(18))
    mobile_phone:             Mapped[str | None]       = mapped_column(String(18))
    fax:                      Mapped[str | None]       = mapped_column(String(18))
    email:                    Mapped[str | None]       = mapped_column(String(64))
    website:                  Mapped[str | None]       = mapped_column(String(64))

    lead_source:              Mapped[str | None]       = mapped_column(String(96))
    status:                   Mapped[str | None]       = mapped_column(String(32))
    industry:                 Mapped[str | None]       = mapped_column(String(32))
    rating:                   Mapped[str | None]       = mapped_column(String(32))
    annual_revenue:           Mapped[str | None]       = mapped_column(String(32))
    number_of_employees:      Mapped[str | None]       = mapped_column(String(32))

    owner_id:                 Mapped[int | None]       = mapped_column(BigInteger)

    do_not_call:              Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    has_opted_out_of_fax:     Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    has_opted_out_of_email:   Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    is_unread_by_owner:       Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    is_deleted:               Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))

    is_converted:             Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    converted_date:           Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    converted_account_id:     Mapped[int | None]       = mapped_column(BigInteger)
    converted_contact_id:     Mapped[int | None]       = mapped_column(BigInteger)
    converted_opportunity_id: Mapped[int | None]       = mapped_column(BigInteger)

    activity_date:            Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    transfer_date:            Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())

    operating_systems:        Mapped[str | None]       = mapped_column(Text)
    master_record_ref:        Mapped[str | None]       = mapped_column(String(18))

    updated_at:              Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by_id:           Mapped[int | None]       = mapped_column(BigInteger)
    created_at:               Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id:            Mapped[int | None]       = mapped_column(BigInteger)


# -----------------------------------------------------------------------------

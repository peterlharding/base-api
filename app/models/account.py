#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  account - db/schema/create/account.sql
"""
# -----------------------------------------------------------------------------

import uuid

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Identity, Index, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column


# -----------------------------------------------------------------------------

from app.models.base import Base


# -----------------------------------------------------------------------------

class Account(Base):
    __tablename__ = "account"
    __table_args__ = (
        # one per foreign key: Postgres indexes the parent side only,
        # so without these a parent delete scans this table
        Index("account_owner_id_idx", "owner_id"),
        Index("account_parent_id_idx", "parent_id"),
    )

    id:                   Mapped[int]              = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    guid:                 Mapped[uuid.UUID | None] = mapped_column(Uuid)

    name:                 Mapped[str | None]       = mapped_column(String(128))
    type:                 Mapped[str | None]       = mapped_column(String(32))
    description:          Mapped[str | None]       = mapped_column(Text)
    notes:                Mapped[str | None]       = mapped_column(Text)

    record_type_ref:      Mapped[uuid.UUID | None] = mapped_column(Uuid)
    parent_id:            Mapped[int | None]       = mapped_column(BigInteger, ForeignKey("account.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    billing_street:       Mapped[str | None]       = mapped_column(Text)
    billing_city:         Mapped[str | None]       = mapped_column(String(32))
    billing_state:        Mapped[str | None]       = mapped_column(String(20))
    billing_postal_code:  Mapped[str | None]       = mapped_column(String(10))
    billing_country:      Mapped[str | None]       = mapped_column(String(32))

    shipping_street:      Mapped[str | None]       = mapped_column(Text)
    shipping_city:        Mapped[str | None]       = mapped_column(String(32))
    shipping_state:       Mapped[str | None]       = mapped_column(String(20))
    shipping_postal_code: Mapped[str | None]       = mapped_column(String(10))
    shipping_country:     Mapped[str | None]       = mapped_column(String(32))

    phone:                Mapped[str | None]       = mapped_column(String(18))
    fax:                  Mapped[str | None]       = mapped_column(String(18))

    account_number:       Mapped[str | None]       = mapped_column(String(32))
    website:              Mapped[str | None]       = mapped_column(Text)
    sic:                  Mapped[str | None]       = mapped_column(String(32))
    industry:             Mapped[str | None]       = mapped_column(String(32))
    annual_revenue:       Mapped[str | None]       = mapped_column(String(32))
    number_of_employees:  Mapped[str | None]       = mapped_column(String(32))
    ownership:            Mapped[str | None]       = mapped_column(String(32))
    ticker_symbol:        Mapped[str | None]       = mapped_column(String(18))
    rating:               Mapped[str | None]       = mapped_column(String(18))
    site:                 Mapped[str | None]       = mapped_column(Text)

    owner_id:             Mapped[int | None]       = mapped_column(BigInteger, ForeignKey("application_user.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    is_deleted:           Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))

    last_activity_date:   Mapped[date | None]      = mapped_column(Date)
    operating_systems:    Mapped[str | None]       = mapped_column(Text, server_default=text("''"))

    created_at:           Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id:        Mapped[int | None]       = mapped_column(BigInteger)
    updated_at:           Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by_id:        Mapped[int | None]       = mapped_column(BigInteger)


# -----------------------------------------------------------------------------

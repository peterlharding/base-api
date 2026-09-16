#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  opportunity - db/schema/create/opportunity.sql

  amount, probability and the other figures are varchar(32) in the schema.
"""
# -----------------------------------------------------------------------------

import uuid

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# -----------------------------------------------------------------------------

class Opportunity(Base):
    __tablename__ = "opportunity"

    id:                         Mapped[int]              = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    guid:                       Mapped[uuid.UUID | None] = mapped_column(Uuid)

    name:                       Mapped[str | None]       = mapped_column(String(128))
    description:                Mapped[str | None]       = mapped_column(Text)

    stage_name:                 Mapped[str | None]       = mapped_column(String(32))
    amount:                     Mapped[str | None]       = mapped_column(String(32))
    probability:                Mapped[str | None]       = mapped_column(String(32))
    expected_revenue:           Mapped[str | None]       = mapped_column(String(32))
    total_opportunity_quantity: Mapped[str | None]       = mapped_column(String(32))
    type:                       Mapped[str | None]       = mapped_column(String(64))
    next_step:                  Mapped[str | None]       = mapped_column(String(32))

    account_id:                 Mapped[int | None]       = mapped_column(BigInteger, ForeignKey("account.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    owner_id:                   Mapped[int | None]       = mapped_column(BigInteger, ForeignKey("application_user.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    lead_source:                Mapped[str | None]       = mapped_column(Text)

    is_private:                 Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    is_closed:                  Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    is_won:                     Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    is_deleted:                 Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))

    forecast_category:          Mapped[str | None]       = mapped_column(String(32))
    campaign_ref:               Mapped[uuid.UUID | None] = mapped_column(Uuid)
    has_opportunity_line_item:  Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))

    pricebook_ref:              Mapped[uuid.UUID | None] = mapped_column(Uuid)

    close_date:                 Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_activity_date:         Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())

    fiscal_year:                Mapped[str | None]       = mapped_column(String(32))
    fiscal_quarter:             Mapped[str | None]       = mapped_column(String(32))

    updated_at:                Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by_id:             Mapped[int | None]       = mapped_column(BigInteger)
    created_at:                 Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id:              Mapped[int | None]       = mapped_column(BigInteger)


# -----------------------------------------------------------------------------

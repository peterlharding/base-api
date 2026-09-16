#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  quote - db/schema/create/quote.sql
"""
# -----------------------------------------------------------------------------

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Identity, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# -----------------------------------------------------------------------------

class Quote(Base):
    __tablename__ = "quote"

    id:             Mapped[int]            = mapped_column(BigInteger, Identity(always=True), primary_key=True)

    quote_date:     Mapped[date | None]    = mapped_column(Date)
    quote_amount:   Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    quoter:         Mapped[str]            = mapped_column(String(64))
    quoter_id:      Mapped[int | None]     = mapped_column(BigInteger)

    account_id:     Mapped[int | None]     = mapped_column(BigInteger)
    company:        Mapped[str | None]     = mapped_column(String(80))

    contact_id:     Mapped[int | None]     = mapped_column(BigInteger)
    contact:        Mapped[str | None]     = mapped_column(String(32))

    comment:        Mapped[str | None]     = mapped_column(Text, server_default=text("''"))
    description:    Mapped[str | None]     = mapped_column(Text, server_default=text("''"))

    order_no:       Mapped[str | None]     = mapped_column(String(32))
    order_date:     Mapped[date | None]    = mapped_column(Date)
    order_amount:   Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    invoice_no:     Mapped[str | None]     = mapped_column(String(32))
    invoice_date:   Mapped[date | None]    = mapped_column(Date)
    invoice_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    status:         Mapped[str | None]     = mapped_column(String(16), server_default=text("'Active'"))
    doc_path:       Mapped[str | None]     = mapped_column(Text)

    updated_at:    Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by_id: Mapped[int | None]     = mapped_column(BigInteger)
    created_at:     Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id:  Mapped[int | None]     = mapped_column(BigInteger)


# -----------------------------------------------------------------------------

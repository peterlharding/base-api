#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  event - db/schema/create/event.sql

  guid, who_ref, what_ref, account_id, owner_id and recurrence_activity_id are
  varchar(18) Salesforce-style references, not integer ids.
"""
# -----------------------------------------------------------------------------

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Identity, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# -----------------------------------------------------------------------------

class Event(Base):
    __tablename__ = "event"

    id:                          Mapped[int]         = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    guid:                        Mapped[str | None]  = mapped_column(String(18))

    who_ref:                     Mapped[str | None]  = mapped_column(String(18))
    what_ref:                    Mapped[str | None]  = mapped_column(String(18))

    subject:                     Mapped[str | None]  = mapped_column(String(128))
    description:                 Mapped[str | None]  = mapped_column(Text)
    location:                    Mapped[str | None]  = mapped_column(String(32))

    type:                        Mapped[str | None]  = mapped_column(String(64))
    show_as:                     Mapped[str | None]  = mapped_column(String(32))

    activity_date:               Mapped[date | None] = mapped_column(Date)
    activity_datetime:           Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())

    is_all_day_event:            Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))

    duration_in_minutes:         Mapped[int | None]  = mapped_column(Integer, server_default=text("0"))

    account_id:                  Mapped[str | None]  = mapped_column(String(18))
    owner_id:                    Mapped[str | None]  = mapped_column(String(18))

    is_group_event:              Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    is_private:                  Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    is_child:                    Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    is_archived:                 Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    is_deleted:                  Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))

    is_recurrence:               Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    recurrence_activity_id:      Mapped[str | None]  = mapped_column(String(18))
    recurrence_start_datetime:   Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())
    recurrence_end_date_only:    Mapped[date | None] = mapped_column(Date)
    recurrence_timezone_sid_key: Mapped[str | None]  = mapped_column(String(32))
    recurrence_type:             Mapped[str | None]  = mapped_column(String(32))
    recurrence_interval:         Mapped[str | None]  = mapped_column(String(32))
    recurrence_day_of_week_mask: Mapped[str | None]  = mapped_column(String(32))
    recurrence_day_of_month:     Mapped[str | None]  = mapped_column(String(32))
    recurrence_instance:         Mapped[str | None]  = mapped_column(String(32))
    recurrence_month_of_year:    Mapped[str | None]  = mapped_column(String(32))

    is_reminder_set:             Mapped[bool | None] = mapped_column(Boolean, server_default=text("false"))
    reminder_datetime:           Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())

    updated_at:                 Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by_id:              Mapped[int | None]  = mapped_column(BigInteger)
    created_at:                  Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id:               Mapped[int | None]  = mapped_column(BigInteger)


# -----------------------------------------------------------------------------

#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  task - db/schema/create/task.sql
"""
# -----------------------------------------------------------------------------

import uuid

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, Integer, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# -----------------------------------------------------------------------------

class Task(Base):
    __tablename__ = "task"

    id:                       Mapped[int]              = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    guid:                     Mapped[uuid.UUID | None] = mapped_column(Uuid)

    subject:                  Mapped[str | None]       = mapped_column(Text)
    description:              Mapped[str | None]       = mapped_column(Text)

    type:                     Mapped[str | None]       = mapped_column(String(64))
    status:                   Mapped[str | None]       = mapped_column(String(32))
    priority:                 Mapped[str | None]       = mapped_column(String(32))

    who_type:                 Mapped[str | None]       = mapped_column(String(32))
    who_id:                   Mapped[int | None]       = mapped_column(BigInteger)
    who_ref:                  Mapped[str | None]       = mapped_column(Text)

    what_type:                Mapped[str | None]       = mapped_column(String(32))
    what_id:                  Mapped[int | None]       = mapped_column(BigInteger)
    what_ref:                 Mapped[str | None]       = mapped_column(Text)

    is_closed:                Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    is_deleted:               Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    is_archived:              Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))

    owner_id:                 Mapped[int | None]       = mapped_column(BigInteger)
    account_id:               Mapped[int | None]       = mapped_column(BigInteger)

    activity_date:            Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())

    call_duration_in_seconds: Mapped[int | None]       = mapped_column(Integer, server_default=text("0"))
    call_type:                Mapped[str | None]       = mapped_column(String(64))
    call_disposition:         Mapped[str | None]       = mapped_column(Text)
    call_object:              Mapped[str | None]       = mapped_column(Text)

    is_reminder_set:          Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    reminder_datetime:        Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())

    updated_at:              Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by_id:           Mapped[int | None]       = mapped_column(BigInteger)
    created_at:               Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id:            Mapped[int | None]       = mapped_column(BigInteger)


# -----------------------------------------------------------------------------

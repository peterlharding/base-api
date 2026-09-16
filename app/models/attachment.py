#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  attachment - db/schema/create/attachment.sql
"""
# -----------------------------------------------------------------------------

import uuid

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, Integer, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column


# -----------------------------------------------------------------------------

from app.models.base import Base


# -----------------------------------------------------------------------------

class Attachment(Base):
    __tablename__ = "attachment"

    id:                     Mapped[int]              = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    guid:                   Mapped[uuid.UUID | None] = mapped_column(Uuid)
    name:                   Mapped[str | None]       = mapped_column(String(128))

    content_type:           Mapped[str | None]       = mapped_column(String(32))
    body_length:            Mapped[int | None]       = mapped_column(Integer, server_default=text("0"))
    body_length_compressed: Mapped[int | None]       = mapped_column(Integer, server_default=text("0"))

    parent_id:              Mapped[int | None]       = mapped_column(BigInteger)
    owner_id:               Mapped[int | None]       = mapped_column(BigInteger)

    is_deleted:             Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    is_private:             Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))

    updated_at:            Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by_id:         Mapped[int | None]       = mapped_column(BigInteger)
    created_at:             Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id:          Mapped[int | None]       = mapped_column(BigInteger)


# -----------------------------------------------------------------------------

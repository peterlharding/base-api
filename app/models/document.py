#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  document - db/schema/create/document.sql
"""
# -----------------------------------------------------------------------------

import uuid

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, Integer, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# -----------------------------------------------------------------------------

class Document(Base):
    __tablename__ = "document"

    id:                     Mapped[int]              = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    guid:                   Mapped[uuid.UUID | None] = mapped_column(Uuid)

    name:                   Mapped[str | None]       = mapped_column(String(128))
    content_type:           Mapped[str | None]       = mapped_column(String(32))
    type:                   Mapped[str | None]       = mapped_column(String(16))

    url:                    Mapped[str | None]       = mapped_column(Text)
    description:            Mapped[str | None]       = mapped_column(Text)
    keywords:               Mapped[str | None]       = mapped_column(Text)

    body_length:            Mapped[int | None]       = mapped_column(Integer, server_default=text("0"))
    body_length_compressed: Mapped[int | None]       = mapped_column(Integer, server_default=text("0"))

    author_id:              Mapped[int | None]       = mapped_column(BigInteger, ForeignKey("application_user.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    author_details:         Mapped[str | None]       = mapped_column(Text)

    folder_ref:             Mapped[uuid.UUID | None] = mapped_column(Uuid)

    is_deleted:             Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    is_public:              Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    is_internal_use_only:   Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))

    updated_at:            Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by_id:         Mapped[int | None]       = mapped_column(BigInteger)
    created_at:             Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id:          Mapped[int | None]       = mapped_column(BigInteger)


# -----------------------------------------------------------------------------

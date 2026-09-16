#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  note - db/schema/create/note.sql
"""
# -----------------------------------------------------------------------------

import uuid

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, Index, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# -----------------------------------------------------------------------------

class Note(Base):
    __tablename__ = "note"
    __table_args__ = (
        # one per foreign key: Postgres indexes the parent side only,
        # so without these a parent delete scans this table
        Index("note_owner_id_idx", "owner_id"),
    )

    id:             Mapped[int]              = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    guid:           Mapped[uuid.UUID | None] = mapped_column(Uuid)

    title:          Mapped[str | None]       = mapped_column(Text)
    body:           Mapped[str | None]       = mapped_column(Text)

    parent_type:    Mapped[str | None]       = mapped_column(String(64))
    parent_id:      Mapped[int | None]       = mapped_column(BigInteger)

    is_deleted:     Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))
    is_private:     Mapped[bool | None]      = mapped_column(Boolean, server_default=text("false"))

    owner_id:       Mapped[int | None]       = mapped_column(BigInteger, ForeignKey("application_user.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    updated_at:    Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by_id: Mapped[int | None]       = mapped_column(BigInteger)
    created_at:     Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id:  Mapped[int | None]       = mapped_column(BigInteger)


# -----------------------------------------------------------------------------

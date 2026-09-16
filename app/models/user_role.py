#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
  user_role - db/schema/create/user_role.sql
"""
# -----------------------------------------------------------------------------

import uuid

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# -----------------------------------------------------------------------------

class UserRole(Base):
    __tablename__ = "user_role"

    id:                                   Mapped[int]              = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    guid:                                 Mapped[uuid.UUID | None] = mapped_column(Uuid)
    name:                                 Mapped[str | None]       = mapped_column(String(64))

    parent_role_id:                       Mapped[int | None]       = mapped_column(BigInteger, ForeignKey("user_role.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    rollup_description:                   Mapped[str | None]       = mapped_column(Text)

    opportunity_access_for_account_owner: Mapped[str | None]       = mapped_column(String(20), server_default=text("'Edit'"))
    case_access_for_account_owner:        Mapped[str | None]       = mapped_column(String(20), server_default=text("'Edit'"))
    contact_access_for_account_owner:     Mapped[str | None]       = mapped_column(String(20), server_default=text("'Edit'"))

    forecast_user_id:                     Mapped[int | None]       = mapped_column(BigInteger, ForeignKey("application_user.id", ondelete="SET NULL", deferrable=True, initially="IMMEDIATE"))
    portal_account_ref:                   Mapped[str | None]       = mapped_column(String(18))
    portal_type:                          Mapped[str | None]       = mapped_column(String(20))

    updated_at:                          Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by_id:                       Mapped[int | None]       = mapped_column(BigInteger)
    created_at:                           Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_id:                        Mapped[int | None]       = mapped_column(BigInteger)


# -----------------------------------------------------------------------------

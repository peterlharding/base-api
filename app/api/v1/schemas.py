#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Pydantic schemas for the version 1 API.

Mirrors application_user minus the server-managed parts: ``password`` is
never exposed, and the audit columns (created_date / last_modified_date /
last_login_date and the *_by_id stamps) are only read back, never written.
"""
# -----------------------------------------------------------------------------

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# -----------------------------------------------------------------------------

class UserBase(BaseModel):
    """Every writable business field of application_user."""

    ref: UUID | None = None
    username: str | None = None
    user_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company_name: str | None = None
    division: str | None = None
    department: str | None = None
    title: str | None = None
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    email: str | None = None
    phone: str | None = None
    fax: str | None = None
    mobile_phone: str | None = None
    alias: str | None = None
    is_active: bool | None = None
    timezone_key: str | None = None
    user_role_id: int | None = None
    locale_key: str | None = None
    email_encoding_key: str | None = None
    profile_id: int | None = None
    employee_number: str | None = None
    user_type: str | None = None
    start_day: int | None = None
    end_day: int | None = None
    language_locale_key: str | None = None
    delegated_approver_id: int | None = None


# -----------------------------------------------------------------------------

class UserCreate(UserBase):
    """Payload for POST /users; only username is mandatory."""

    username: str


# -----------------------------------------------------------------------------

class UserUpdate(UserBase):
    """Payload for PUT /users/{id}; all fields optional (patch-style)."""


# -----------------------------------------------------------------------------

class User(UserBase):
    """A user as returned by the API, including id and audit timestamps."""

    id: int
    last_login_date: datetime | None = None
    created_date: datetime | None = None
    last_modified_date: datetime | None = None


# -----------------------------------------------------------------------------

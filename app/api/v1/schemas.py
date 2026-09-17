#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Pydantic schemas for the version 1 API.

Mirrors application_user minus the server-managed parts: ``hashed_password``
is never exposed.  created_at / updated_at / last_login_date and the
created_by_id / updated_by_id stamps are read back but never written: the
stamps come from the bearer token, so a client cannot claim to be someone
else.
"""
# -----------------------------------------------------------------------------

from datetime import date, datetime
from decimal import Decimal
from ipaddress import IPv4Address, IPv6Address
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# -----------------------------------------------------------------------------

class UserBase(BaseModel):
    """Every writable business field of application_user."""

    guid: UUID | None = None
    username: str | None = None
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
    phone_extension: str | None = None
    fax: str | None = None
    mobile_phone: str | None = None
    alias: str | None = None
    is_active: bool | None = None
    timezone_sid_key: str | None = None
    user_role_id: int | None = None
    locale_sid_key: str | None = None
    email_encoding_key: str | None = None
    receives_info_emails: bool | None = None
    receives_admin_info_emails: bool | None = None
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

    model_config = ConfigDict(extra="forbid")

    username: str


# -----------------------------------------------------------------------------

class UserUpdate(UserBase):
    """Payload for PUT /users/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class User(UserBase):
    """A user as returned by the API, including id and audit timestamps."""

    id: int
    last_login_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Contact
#
# Mirrors contact minus the server-managed parts: created_at / updated_at are
# read back but never written, and the *_by_id audit stamps are neither.
# `guid` here is an 18-character Salesforce-style id, not a uuid.


class ContactBase(BaseModel):
    """Every writable business field of contact."""

    guid: str | None = None

    salutation: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    title: str | None = None
    department: str | None = None
    account_id: int | None = None

    description: str | None = None
    notes: str | None = None

    other_street: str | None = None
    other_city: str | None = None
    other_state: str | None = None
    other_postal_code: str | None = None
    other_country: str | None = None

    mailing_street: str | None = None
    mailing_city: str | None = None
    mailing_state: str | None = None
    mailing_postal_code: str | None = None
    mailing_country: str | None = None

    phone: str | None = None
    fax: str | None = None
    mobile_phone: str | None = None
    home_phone: str | None = None
    other_phone: str | None = None
    email: str | None = None

    assistant_name: str | None = None
    assistant_phone: str | None = None

    reports_to_id: int | None = None
    owner_id: int | None = None

    lead_source: str | None = None
    birthdate: date | None = None

    do_not_call: bool | None = None
    has_opted_out_of_email: bool | None = None
    has_opted_out_of_fax: bool | None = None

    last_activity_date: datetime | None = None
    is_deleted: bool | None = None


# -----------------------------------------------------------------------------

class ContactCreate(ContactBase):
    """Payload for POST /contacts; only last_name is mandatory."""

    model_config = ConfigDict(extra="forbid")

    last_name: str


# -----------------------------------------------------------------------------

class ContactUpdate(ContactBase):
    """Payload for PUT /contacts/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class Contact(ContactBase):
    """A contact as returned by the API, including id and audit timestamps."""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------
# Account
#
# Same split as Contact.  `guid` and `record_type_ref` are real uuids here.


class AccountBase(BaseModel):
    """Every writable business field of account."""

    guid: UUID | None = None

    name: str | None = None
    type: str | None = None
    description: str | None = None
    notes: str | None = None

    record_type_ref: UUID | None = None
    parent_id: int | None = None

    billing_street: str | None = None
    billing_city: str | None = None
    billing_state: str | None = None
    billing_postal_code: str | None = None
    billing_country: str | None = None

    shipping_street: str | None = None
    shipping_city: str | None = None
    shipping_state: str | None = None
    shipping_postal_code: str | None = None
    shipping_country: str | None = None

    phone: str | None = None
    fax: str | None = None

    account_number: str | None = None
    website: str | None = None
    sic: str | None = None
    industry: str | None = None
    annual_revenue: str | None = None
    number_of_employees: str | None = None
    ownership: str | None = None
    ticker_symbol: str | None = None
    rating: str | None = None
    site: str | None = None

    owner_id: int | None = None
    is_deleted: bool | None = None

    last_activity_date: date | None = None
    operating_systems: str | None = None


# -----------------------------------------------------------------------------

class AccountCreate(AccountBase):
    """Payload for POST /accounts; only name is mandatory."""

    model_config = ConfigDict(extra="forbid")

    name: str


# -----------------------------------------------------------------------------

class AccountUpdate(AccountBase):
    """Payload for PUT /accounts/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class Account(AccountBase):
    """An account as returned by the API, including id and audit timestamps."""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Task
#
# Mirrors task minus the server-managed parts: created_at /
# updated_at are read back but never written, and the *_by_id audit stamps are
# neither.


class TaskBase(BaseModel):
    """Every writable business field of task."""

    guid: UUID | None = None
    subject: str | None = None
    description: str | None = None
    type: str | None = None
    status: str | None = None
    priority: str | None = None
    who_type: str | None = None
    who_id: int | None = None
    who_ref: str | None = None
    what_type: str | None = None
    what_id: int | None = None
    what_ref: str | None = None
    is_closed: bool | None = None
    is_deleted: bool | None = None
    is_archived: bool | None = None
    owner_id: int | None = None
    account_id: int | None = None
    activity_date: datetime | None = None
    call_duration_in_seconds: int | None = None
    call_type: str | None = None
    call_disposition: str | None = None
    call_object: str | None = None
    is_reminder_set: bool | None = None
    reminder_datetime: datetime | None = None


# -----------------------------------------------------------------------------

class TaskCreate(TaskBase):
    """Payload for POST /tasks; only subject is mandatory."""

    model_config = ConfigDict(extra="forbid")

    subject: str


# -----------------------------------------------------------------------------

class TaskUpdate(TaskBase):
    """Payload for PUT /tasks/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class Task(TaskBase):
    """A task as returned by the API, including id and audit timestamps."""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------
# Event
#
# Mirrors event minus the server-managed parts: created_at /
# updated_at are read back but never written, and the *_by_id audit stamps are
# neither.


class EventBase(BaseModel):
    """Every writable business field of event."""

    guid: str | None = None
    who_ref: str | None = None
    what_ref: str | None = None
    subject: str | None = None
    description: str | None = None
    location: str | None = None
    type: str | None = None
    show_as: str | None = None
    activity_date: date | None = None
    activity_datetime: datetime | None = None
    is_all_day_event: bool | None = None
    duration_in_minutes: int | None = None
    account_id: str | None = None
    owner_id: str | None = None
    is_group_event: bool | None = None
    is_private: bool | None = None
    is_child: bool | None = None
    is_archived: bool | None = None
    is_deleted: bool | None = None
    is_recurrence: bool | None = None
    recurrence_activity_id: str | None = None
    recurrence_start_datetime: datetime | None = None
    recurrence_end_date_only: date | None = None
    recurrence_timezone_sid_key: str | None = None
    recurrence_type: str | None = None
    recurrence_interval: str | None = None
    recurrence_day_of_week_mask: str | None = None
    recurrence_day_of_month: str | None = None
    recurrence_instance: str | None = None
    recurrence_month_of_year: str | None = None
    is_reminder_set: bool | None = None
    reminder_datetime: datetime | None = None


# -----------------------------------------------------------------------------

class EventCreate(EventBase):
    """Payload for POST /events; only subject is mandatory."""

    model_config = ConfigDict(extra="forbid")

    subject: str


# -----------------------------------------------------------------------------

class EventUpdate(EventBase):
    """Payload for PUT /events/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class Event(EventBase):
    """A event as returned by the API, including id and audit timestamps."""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------
# Document
#
# Mirrors document minus the server-managed parts: created_at /
# updated_at are read back but never written, and the *_by_id audit stamps are
# neither.


class DocumentBase(BaseModel):
    """Every writable business field of document."""

    guid: UUID | None = None
    name: str | None = None
    content_type: str | None = None
    type: str | None = None
    url: str | None = None
    description: str | None = None
    keywords: str | None = None
    body_length: int | None = None
    body_length_compressed: int | None = None
    author_id: int | None = None
    author_details: str | None = None
    folder_ref: UUID | None = None
    is_deleted: bool | None = None
    is_public: bool | None = None
    is_internal_use_only: bool | None = None


# -----------------------------------------------------------------------------

class DocumentCreate(DocumentBase):
    """Payload for POST /documents; only name is mandatory."""

    model_config = ConfigDict(extra="forbid")

    name: str


# -----------------------------------------------------------------------------

class DocumentUpdate(DocumentBase):
    """Payload for PUT /documents/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class Document(DocumentBase):
    """A document as returned by the API, including id and audit timestamps."""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------
# Note
#
# Mirrors note minus the server-managed parts: created_at /
# updated_at are read back but never written, and the *_by_id audit stamps are
# neither.


class NoteBase(BaseModel):
    """Every writable business field of note."""

    guid: UUID | None = None
    title: str | None = None
    body: str | None = None
    parent_type: str | None = None
    parent_id: int | None = None
    is_deleted: bool | None = None
    is_private: bool | None = None
    owner_id: int | None = None


# -----------------------------------------------------------------------------

class NoteCreate(NoteBase):
    """Payload for POST /notes; only title is mandatory."""

    model_config = ConfigDict(extra="forbid")

    title: str


# -----------------------------------------------------------------------------

class NoteUpdate(NoteBase):
    """Payload for PUT /notes/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class Note(NoteBase):
    """A note as returned by the API, including id and audit timestamps."""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Opportunity
#
# Mirrors opportunity minus the server-managed parts: created_at /
# updated_at are read back but never written, and the *_by_id audit stamps are
# neither.


class OpportunityBase(BaseModel):
    """Every writable business field of opportunity."""

    guid: UUID | None = None
    name: str | None = None
    description: str | None = None
    stage_name: str | None = None
    amount: str | None = None
    probability: str | None = None
    expected_revenue: str | None = None
    total_opportunity_quantity: str | None = None
    type: str | None = None
    next_step: str | None = None
    account_id: int | None = None
    owner_id: int | None = None
    lead_source: str | None = None
    is_private: bool | None = None
    is_closed: bool | None = None
    is_won: bool | None = None
    is_deleted: bool | None = None
    forecast_category: str | None = None
    campaign_ref: UUID | None = None
    has_opportunity_line_item: bool | None = None
    pricebook_ref: UUID | None = None
    close_date: datetime | None = None
    last_activity_date: datetime | None = None
    fiscal_year: str | None = None
    fiscal_quarter: str | None = None


# -----------------------------------------------------------------------------

class OpportunityCreate(OpportunityBase):
    """Payload for POST /opportunities; only name is mandatory
    (api-level: the column is nullable in the database).
    """

    model_config = ConfigDict(extra="forbid")

    name: str


# -----------------------------------------------------------------------------

class OpportunityUpdate(OpportunityBase):
    """Payload for PUT /opportunities/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class Opportunity(OpportunityBase):
    """Opportunity as returned by the API, including id and audit timestamps."""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------
# Lead
#
# Mirrors lead minus the server-managed parts: created_at /
# updated_at are read back but never written, and the *_by_id audit stamps are
# neither.


class LeadBase(BaseModel):
    """Every writable business field of lead."""

    guid: UUID | None = None
    description: str | None = None
    salutation: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    company: str | None = None
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    phone: str | None = None
    mobile_phone: str | None = None
    fax: str | None = None
    email: str | None = None
    website: str | None = None
    lead_source: str | None = None
    status: str | None = None
    industry: str | None = None
    rating: str | None = None
    annual_revenue: str | None = None
    number_of_employees: str | None = None
    owner_id: int | None = None
    do_not_call: bool | None = None
    has_opted_out_of_fax: bool | None = None
    has_opted_out_of_email: bool | None = None
    is_unread_by_owner: bool | None = None
    is_deleted: bool | None = None
    is_converted: bool | None = None
    converted_date: datetime | None = None
    converted_account_id: int | None = None
    converted_contact_id: int | None = None
    converted_opportunity_id: int | None = None
    activity_date: datetime | None = None
    transfer_date: datetime | None = None
    operating_systems: str | None = None
    master_record_ref: str | None = None


# -----------------------------------------------------------------------------

class LeadCreate(LeadBase):
    """Payload for POST /leads; only last_name is mandatory
    (api-level: the column is nullable in the database).
    """

    model_config = ConfigDict(extra="forbid")

    last_name: str


# -----------------------------------------------------------------------------

class LeadUpdate(LeadBase):
    """Payload for PUT /leads/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class Lead(LeadBase):
    """Lead as returned by the API, including id and audit timestamps."""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------
# Quote
#
# Mirrors quote minus the server-managed parts: created_at /
# updated_at are read back but never written, and the *_by_id audit stamps are
# neither.


class QuoteBase(BaseModel):
    """Every writable business field of quote."""

    quote_date: date | None = None
    quote_amount: Decimal | None = None
    quoter: str | None = None
    quoter_id: int | None = None
    account_id: int | None = None
    company: str | None = None
    contact_id: int | None = None
    contact: str | None = None
    comment: str | None = None
    description: str | None = None
    order_no: str | None = None
    order_date: date | None = None
    order_amount: Decimal | None = None
    invoice_no: str | None = None
    invoice_date: date | None = None
    invoice_amount: Decimal | None = None
    status: str | None = None
    doc_path: str | None = None


# -----------------------------------------------------------------------------

class QuoteCreate(QuoteBase):
    """Payload for POST /quotes; only quoter is mandatory
    (quoter is NOT NULL in the database, so this one is not a choice).
    """

    model_config = ConfigDict(extra="forbid")

    quoter: str


# -----------------------------------------------------------------------------

class QuoteUpdate(QuoteBase):
    """Payload for PUT /quotes/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class Quote(QuoteBase):
    """Quote as returned by the API, including id and audit timestamps."""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------
# Access
#
# Mirrors access, which carries no audit columns at all - no
# created_at / updated_at / *_by_id, and so no set_updated_at trigger.


class AccessBase(BaseModel):
    """Every writable business field of access."""

    access_type: str | None = None
    reference_name: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    owner_id: int | None = None
    user_id: int | None = None
    last_referenced_date: datetime | None = None


# -----------------------------------------------------------------------------

class AccessCreate(AccessBase):
    """Payload for POST /access; only reference_type is mandatory
    (api-level: every column on this table is nullable).
    """

    model_config = ConfigDict(extra="forbid")

    reference_type: str


# -----------------------------------------------------------------------------

class AccessUpdate(AccessBase):
    """Payload for PUT /access/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class Access(AccessBase):
    """Access as returned by the API.  No audit timestamps on this table."""

    id: int


# -----------------------------------------------------------------------------
# Attachment
#
# Mirrors attachment minus the server-managed parts: created_at /
# updated_at are read back but never written, and the *_by_id audit stamps are
# neither.


class AttachmentBase(BaseModel):
    """Every writable business field of attachment."""

    guid: UUID | None = None
    name: str | None = None
    content_type: str | None = None
    body_length: int | None = None
    body_length_compressed: int | None = None
    parent_id: int | None = None
    owner_id: int | None = None
    is_deleted: bool | None = None
    is_private: bool | None = None


# -----------------------------------------------------------------------------

class AttachmentCreate(AttachmentBase):
    """Payload for POST /attachments; only name is mandatory
    (api-level: the column is nullable in the database).
    """

    model_config = ConfigDict(extra="forbid")

    name: str


# -----------------------------------------------------------------------------

class AttachmentUpdate(AttachmentBase):
    """Payload for PUT /attachments/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class Attachment(AttachmentBase):
    """Attachment as returned by the API, including id and audit timestamps."""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# UserRole
#
# Mirrors user_role minus the server-managed parts: created_at / updated_at
# are read back but never written, and the *_by_id audit stamps are neither.


class UserRoleBase(BaseModel):
    """Every writable business field of user_role."""

    guid: UUID | None = None
    name: str | None = None
    parent_role_id: int | None = None
    rollup_description: str | None = None
    opportunity_access_for_account_owner: str | None = None
    case_access_for_account_owner: str | None = None
    contact_access_for_account_owner: str | None = None
    forecast_user_id: int | None = None
    portal_account_ref: str | None = None
    portal_type: str | None = None


# -----------------------------------------------------------------------------

class UserRoleCreate(UserRoleBase):
    """Payload for POST /user-roles; only name is mandatory
    (api-level: the column is nullable in the database).
    """

    model_config = ConfigDict(extra="forbid")

    name: str


# -----------------------------------------------------------------------------

class UserRoleUpdate(UserRoleBase):
    """Payload for PUT /user-roles/{id}; all fields optional (patch-style)."""

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------

class UserRole(UserRoleBase):
    """A user role as returned by the API, including id and audit timestamps."""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# LoginSession
#
# Read-only: the API records a session when it issues a token, so there is no
# Create or Update schema.  session_token_hash is deliberately absent - it is
# a digest of a credential, and a read endpoint has no business returning it.


class LoginSession(BaseModel):
    """A sign-in, as returned by the API."""

    id: int
    user_id: int
    workstation: str | None = None
    # INET deserialises as an ip address object, not a str; pydantic
    # serialises these back to a string in the JSON response.
    ip_address: IPv4Address | IPv6Address | None = None
    user_agent: str | None = None
    data: dict | None = None
    started: datetime | None = None
    last_seen: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None


# -----------------------------------------------------------------------------
# AuditLog
#
# Append-only: create and read, never update or delete.  user_id is absent
# from the create schema because it is taken from the bearer token - a client
# does not get to say who did something.


class AuditLogCreate(BaseModel):
    """Payload for POST /audit-log."""

    model_config = ConfigDict(extra="forbid")

    application: str
    reference_type: int
    reference_id: int
    event: str
    description: str
    reference: str | None = None


# -----------------------------------------------------------------------------

class AuditLog(BaseModel):
    """An audit entry as returned by the API."""

    id: int
    application: str
    reference_type: int
    reference_id: int
    reference: str | None = None
    event: str
    description: str
    user_id: str
    created_at: datetime | None = None


# -----------------------------------------------------------------------------
# InstanceMetadata
#
# A singleton describing the backend the caller is talking to.  db_version
# and release come from the table; app_version and alembic_revision are read
# at runtime, because a value stamped into a row goes stale the moment the
# application is upgraded without a migration.


class InstanceMetadata(BaseModel):
    """What backend am I talking to."""

    release: str
    app_version: str
    db_version: str
    alembic_revision: str | None = None
    notes: str = ""
    updated_at: datetime | None = None


# -----------------------------------------------------------------------------

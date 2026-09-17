#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Endpoints for audit_log, served under /api/v1/audit-log.

Read-only.  The API writes these rows itself, in app/api/v1/crud.py, which
every mutation already passes through - an entry a client can compose is one
it can fabricate or omit, and one a route can forget to send.

Mutations only.  Reads are not recorded: on a CRM the list endpoints would
produce more rows than everything else combined.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import get_or_404
from app.auth.bearer import jwt_bearer
from app.models      import AuditLog
from app.db.session  import get_db


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/audit-log", tags=["audit-log"])

_LABEL = "audit entry"


# -----------------------------------------------------------------------------

@router.get("", response_model=list[schemas.AuditLog],
            dependencies=[Depends(jwt_bearer)])
def list_audit_log(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    application: str | None = Query(default=None),
    reference_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
) -> list[AuditLog]:
    """Page through audit_log, newest first."""
    stmt = select(AuditLog)

    if application is not None:
        stmt = stmt.where(AuditLog.application == application)
    if reference_type is not None:
        stmt = stmt.where(AuditLog.reference_type == reference_type)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)

    stmt = stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())

    return list(db.scalars(stmt.limit(limit).offset(offset)))


# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------

@router.get("/{audit_log_pk}", response_model=schemas.AuditLog,
            dependencies=[Depends(jwt_bearer)])
def get_audit_entry(audit_log_pk: int, db: Session = Depends(get_db)) -> AuditLog:
    """Fetch a single entry by surrogate key."""
    return get_or_404(db, AuditLog, audit_log_pk, _LABEL)


# -----------------------------------------------------------------------------

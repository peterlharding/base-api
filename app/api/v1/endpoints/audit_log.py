#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Endpoints for audit_log, served under /api/v1/audit-log.

Append-only: GET and POST, never PUT or DELETE.  An audit trail that the
people it records can edit is not one.

``user_id`` is taken from the bearer token, not the payload.  A client does
not get to say who performed an action.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import commit, get_or_404
from app.auth.bearer import jwt_bearer
from app.models      import ApplicationUser, AuditLog
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
    event: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
) -> list[AuditLog]:
    """Page through audit_log, newest first."""
    stmt = select(AuditLog)

    if application is not None:
        stmt = stmt.where(AuditLog.application == application)
    if event is not None:
        stmt = stmt.where(AuditLog.event == event)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)

    stmt = stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())

    return list(db.scalars(stmt.limit(limit).offset(offset)))


# -----------------------------------------------------------------------------

@router.post("", response_model=schemas.AuditLog, status_code=status.HTTP_201_CREATED)
def create_audit_entry(
    payload: schemas.AuditLogCreate,
    user: ApplicationUser = Depends(jwt_bearer),
    db: Session = Depends(get_db),
) -> AuditLog:
    """Record an entry, attributed to the token holder.

    Takes the user from the dependency rather than `dependencies=[...]`,
    because here the identity is the point: it is what gets written.
    """
    entry = AuditLog(**payload.model_dump(exclude_unset=True), user_id=str(user.guid))
    db.add(entry)
    commit(db, AuditLog, _LABEL)
    db.refresh(entry)
    return entry


# -----------------------------------------------------------------------------

@router.get("/{audit_log_pk}", response_model=schemas.AuditLog,
            dependencies=[Depends(jwt_bearer)])
def get_audit_entry(audit_log_pk: int, db: Session = Depends(get_db)) -> AuditLog:
    """Fetch a single entry by surrogate key."""
    return get_or_404(db, AuditLog, audit_log_pk, _LABEL)


# -----------------------------------------------------------------------------

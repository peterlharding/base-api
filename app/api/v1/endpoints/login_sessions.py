#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Read-only endpoints for login_session, served under /api/v1/login-sessions.

The API writes these rows itself when it issues a token, so there is no POST,
PUT or DELETE: a front end that reports its own sessions can decline to, or
report someone else's.

``session_token_hash`` is never returned.  It is a digest of a credential,
and nothing reading the session list needs it.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import get_or_404
from app.auth.bearer import jwt_bearer
from app.models      import LoginSession
from app.db.session  import get_db


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/login-sessions", tags=["login-sessions"])

_LABEL = "login session"


# -----------------------------------------------------------------------------

@router.get("", response_model=list[schemas.LoginSession],
            dependencies=[Depends(jwt_bearer)])
def list_login_sessions(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: int | None = Query(default=None, description="only this user's sessions"),
    active: bool | None = Query(default=None, description="unrevoked and unexpired only"),
) -> list[LoginSession]:
    """Page through login_session, newest first.

    Newest first rather than in id order: a session list is read to see what
    is happening now, and the useful rows are at the recent end.
    """
    from datetime import datetime, timezone

    stmt = select(LoginSession)

    if user_id is not None:
        stmt = stmt.where(LoginSession.user_id == user_id)

    if active is not None:
        now = datetime.now(timezone.utc)
        live = (LoginSession.revoked_at.is_(None)) & (LoginSession.expires_at > now)
        stmt = stmt.where(live if active else ~live)

    stmt = stmt.order_by(LoginSession.started.desc(), LoginSession.id.desc())

    return list(db.scalars(stmt.limit(limit).offset(offset)))


# -----------------------------------------------------------------------------

@router.get("/{login_session_pk}", response_model=schemas.LoginSession,
            dependencies=[Depends(jwt_bearer)])
def get_login_session(login_session_pk: int, db: Session = Depends(get_db)) -> LoginSession:
    """Fetch a single session by surrogate key."""
    return get_or_404(db, LoginSession, login_session_pk, _LABEL)


# -----------------------------------------------------------------------------

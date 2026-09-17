#!/usr/bin/env python
#
#
#
# -----------------------------------------------------------------------------

import re

from datetime import datetime


# -----------------------------------------------------------------------------

from app.logger import logger
from app.db.session import SessionLocal

from app.models import (
    LoginSession,
)


# -----------------------------------------------------------------------------

def format_datetime(value):
    """Format datetime to human-readable string."""
    if not value:
        return ""
    return datetime.strftime(value, "%Y-%m-%d %H:%M:%S")


# -----------------------------------------------------------------------------

def record_login_session(db, user, token: str, request) -> None:
    """Record a sign-in against login_session.

    Written by the API rather than reported by the client: a front end that
    reports its own sessions can decline to, or report someone else's.  The
    endpoints under /api/v1/login-sessions are therefore read-only.

    Only a SHA-256 of the token is stored.  The row is a record that a
    session exists, not a place to recover the credential from - a leaked
    table should not hand out working tokens.

    Failure to record is logged, never raised: an audit trail that can refuse
    a sign-in is worse than one with a gap.
    """
    import hashlib
    import ipaddress

    from datetime import datetime, timezone

    from app.auth.handler import TOKEN_TTL
    from app.models import LoginSession

    host = request.client.host if request.client else None

    # ip_address is INET, so it rejects anything that is not an address -
    # a proxy reporting a hostname, a unix socket, or TestClient's literal
    # "testclient".  Those go in workstation, which is free text, rather
    # than failing the insert and silently losing the sign-in record.
    try:
        ip, workstation = str(ipaddress.ip_address(host)), None
    except ValueError:
        ip, workstation = None, host

    try:
        db.add(LoginSession(
            session_token_hash=hashlib.sha256(token.encode()).digest(),
            user_id=user.id,
            ip_address=ip,
            workstation=workstation,
            user_agent=request.headers.get("user-agent"),
            expires_at=datetime.now(timezone.utc) + TOKEN_TTL,
        ))
        db.commit()

    except Exception as ex:                      # noqa: BLE001 - see docstring
        db.rollback()
        logger.warning("could not record login session for user id %s: %s", user.id, ex)


# -----------------------------------------------------------------------------

def expand_location(mnemonic: str | None) -> str | None:
    """
      Expand a location mnemonic into a human-readable format. An example is S1A2B3L2,
      which would be expanded to "Store 1 - Aisle 2 - Bay 3 - Level 2 (S1A2B3L2)".
      If the mnemonic does not match the expected pattern, it will be returned as-is.
    """
    if not mnemonic:
        return None

    pattern = r'^S(\d+)A(\d+)B(\d+)L(\d+)$'

    match = re.match(pattern, mnemonic.strip().upper())

    if not match:
        return mnemonic

    store, aisle, bay, level = match.groups()

    return f"Store {store} - Aisle {aisle} - Bay {bay} - Level {level} ({mnemonic.strip().upper()})"


# =============================================================================



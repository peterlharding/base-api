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

def log_session(user, ip_addr):

    db      = SessionLocal()

    session = LoginSession()

    session.username = user.username
    session.workstation = ip_addr
    session.started = datetime.now()
    session.data = user.user_id

    next_id = LoginSession.NextId(db)

    session.id            = next_id

    db.add(session)

    print("[log_session]         ***** About to commit session |")

    try:
        db.flush()
        db.commit()
    except Exception as ex:
        db.rollback()
        logger.info("[log_session]          Rolled back after exception |%s|" % ex)
        # return {"result":"failed '%s'" % ex}

    print("[log_session]  Completed...")


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



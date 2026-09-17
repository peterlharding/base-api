#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Apply the retention policy.

Three tables grow without bound, and they do not all age the same way:

    token_blacklist   pruned by expiry - a row only has to outlive the token
                      it revokes, after which the token fails validation on
                      its own.  No policy needed.

    login_session     pruned by age.  A record that somebody signed in stays
                      true after the session ends, so how long to keep it is
                      a decision.  LOGIN_SESSION_RETENTION_DAYS, default 90.
                      A session that has not ended is never deleted.

    audit_log         pruned by age, and off by default.
                      AUDIT_LOG_RETENTION_DAYS, default 0, meaning keep
                      indefinitely: an audit trail that deletes itself on a
                      timer is a weaker guarantee than one that does not.

Nothing runs this on a schedule.  Logout prunes token_blacklist
opportunistically, which covers the common case; the rest wants cron:

    0 3 * * *  cd /path/to/base-api && .venv/bin/python scripts/prune.py

    python scripts/prune.py [--dry-run] [--only TABLE]
"""
# -----------------------------------------------------------------------------

import argparse
import sys

from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, or_, select


# -----------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings                          # noqa: E402
from app.db.session import SessionLocal                           # noqa: E402
from app.models import AuditLog, LoginSession, TokenBlacklist     # noqa: E402


TABLES = ("token_blacklist", "login_session", "audit_log")


# -----------------------------------------------------------------------------

def _counts(session, settings, moment):
    """How many rows each table holds, and how many are prunable."""
    out = {}

    out["token_blacklist"] = (
        session.scalar(select(func.count()).select_from(TokenBlacklist)),
        session.scalar(
            select(func.count()).select_from(TokenBlacklist)
            .where(TokenBlacklist.expiry < moment)
        ),
        "expired",
    )

    days = settings.login_session_retention_days
    cutoff = moment - timedelta(days=days)
    out["login_session"] = (
        session.scalar(select(func.count()).select_from(LoginSession)),
        session.scalar(
            select(func.count()).select_from(LoginSession).where(
                LoginSession.started < cutoff,
                or_(LoginSession.expires_at < moment,
                    LoginSession.revoked_at.is_not(None)),
            )
        ) if days > 0 else 0,
        f"older than {days} days" if days > 0 else "kept indefinitely",
    )

    days = settings.audit_log_retention_days
    out["audit_log"] = (
        session.scalar(select(func.count()).select_from(AuditLog)),
        session.scalar(
            select(func.count()).select_from(AuditLog)
            .where(AuditLog.created_at < moment - timedelta(days=days))
        ) if days > 0 else 0,
        f"older than {days} days" if days > 0 else "kept indefinitely",
    )

    return out


# -----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would be deleted, delete nothing")
    parser.add_argument("--only", choices=TABLES,
                        help="act on one table instead of all three")
    args = parser.parse_args()

    settings = get_settings()
    wanted = (args.only,) if args.only else TABLES
    moment = datetime.now(timezone.utc)

    print(f"{settings.db_name} at {moment:%Y-%m-%d %H:%M} UTC")

    with SessionLocal() as session:
        counts = _counts(session, settings, moment)

        for table in wanted:
            total, prunable, policy = counts[table]

            if args.dry_run:
                print(f"  {table:16} {prunable:>7} of {total:>7} prunable  ({policy})")
                continue

            if table == "token_blacklist":
                removed = TokenBlacklist.prune_expired(session, now=moment)
            elif table == "login_session":
                removed = LoginSession.prune_older_than(
                    session, settings.login_session_retention_days, now=moment)
            else:
                removed = AuditLog.prune_older_than(
                    session, settings.audit_log_retention_days, now=moment)

            print(f"  {table:16} {removed:>7} of {total:>7} deleted    ({policy})")

        if not args.dry_run:
            session.commit()

    return 0


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    raise SystemExit(main())


# -----------------------------------------------------------------------------

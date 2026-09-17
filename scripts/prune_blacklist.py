#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Delete expired rows from token_blacklist.

A blacklist entry only has to outlive the token it revokes: once the expiry
has passed the token fails validation on its own, and the row is answering a
question nobody will ask.

Logout prunes opportunistically, which is enough while people are signing
out.  This is for a deployment where they are not - run it from cron:

    0 * * * *  cd /path/to/base-api && .venv/bin/python scripts/prune_blacklist.py

    python scripts/prune_blacklist.py [--dry-run]
"""
# -----------------------------------------------------------------------------

import argparse
import sys

from pathlib import Path

from sqlalchemy import func, select


# -----------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings        # noqa: E402
from app.db.session import SessionLocal         # noqa: E402
from app.models import TokenBlacklist           # noqa: E402


# -----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would be deleted, delete nothing")
    args = parser.parse_args()

    settings = get_settings()

    with SessionLocal() as session:
        total = session.scalar(select(func.count()).select_from(TokenBlacklist))

        if args.dry_run:
            from datetime import datetime, timezone

            expired = session.scalar(
                select(func.count()).select_from(TokenBlacklist)
                .where(TokenBlacklist.expiry < datetime.now(timezone.utc))
            )
            print(f"{settings.db_name}: {expired} of {total} row(s) are expired")
            return 0

        pruned = TokenBlacklist.prune_expired(session)
        session.commit()

    print(f"{settings.db_name}: pruned {pruned} of {total} row(s)")
    return 0


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    raise SystemExit(main())


# -----------------------------------------------------------------------------

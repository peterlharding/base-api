#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Load the sample data in db/schema/data into the configured database.

Deliberately NOT an alembic migration.  Migrations are schema history that
every environment replays, production included, and these rows are sample
data.  Two further reasons they cannot live in the chain:

  * the test suite truncates every table in Base.metadata after each test,
    while migrations run once per session, so migration-seeded rows survive
    only until the first test finishes;
  * the files assume the rows land on ids 1 and 2 and cross-reference them
    (owner_id, created_by_id, parent_role_id).  Identity values are consumed
    by failed inserts and reset by TRUNCATE, so a replay can silently point
    those references at the wrong rows.

Connects through the application's own Settings, so it follows DB_NAME /
DB_PORT from .env like everything else.

    python scripts/seed.py [--reset]
"""
# -----------------------------------------------------------------------------

import argparse
import sys
from pathlib import Path

from sqlalchemy import text


# -----------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal          # noqa: E402
from app.core.config import get_settings         # noqa: E402


# -----------------------------------------------------------------------------
# Dependency order, not alphabetical: application_user first because every
# other file references users 1 and 2, then user_role and account before the
# records that point at them.  The tables declare no foreign keys, so nothing
# enforces this but the data is wrong without it.

ORDER = [
    "api_credentials",
    "application_user",
    "user_role",
    "account",
    "contact",
    "lead",
    "opportunity",
    "quote",
    "task",
    "event",
    "note",
    "document",
    "attachment",
    "access",
]

_DATA = Path(__file__).resolve().parents[1] / "db" / "schema" / "data"


# -----------------------------------------------------------------------------

def _occupied(session) -> list[str]:
    """Names of target tables that already hold rows."""
    return [
        name for name in ORDER
        if session.execute(text(f'SELECT 1 FROM "{name}" LIMIT 1')).first()
    ]


# -----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="truncate the seeded tables first (RESTART IDENTITY), so ids "
             "land on 1 and 2 as the data files assume",
    )
    args = parser.parse_args()

    settings = get_settings()
    print(f"seeding {settings.db_name} on {settings.db_host}:{settings.db_port}")

    with SessionLocal() as session:
        occupied = _occupied(session)

        if occupied and not args.reset:
            print("refusing to seed: these tables already hold rows:", file=sys.stderr)
            for name in occupied:
                print(f"    {name}", file=sys.stderr)
            print("re-run with --reset to truncate them first.", file=sys.stderr)
            return 1

        # application_user and user_role reference each other, so no ordering
        # of the files satisfies every constraint statement by statement.  The
        # foreign keys are DEFERRABLE, so defer them to COMMIT for this load.
        session.execute(text("SET CONSTRAINTS ALL DEFERRED"))

        if args.reset:
            targets = ", ".join(f'"{name}"' for name in ORDER)
            session.execute(text(f"TRUNCATE {targets} RESTART IDENTITY CASCADE"))
            print(f"  truncated {len(ORDER)} tables")

        for name in ORDER:
            path = _DATA / f"{name}.sql"
            if not path.exists():
                print(f"  missing {path}", file=sys.stderr)
                return 1
            session.execute(text(path.read_text()))
            print(f"  loaded {name}")

        session.commit()

    print("seed complete")
    return 0


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    raise SystemExit(main())


# -----------------------------------------------------------------------------

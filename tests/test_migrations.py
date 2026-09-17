"""Migrations, exercised against data.

Every other test in this suite runs against a database already at head, so a
migration that corrupts existing rows passes all of them.  Migration 0004 did
exactly that - it silently cleared valid self-referencing values while 222
tests stayed green - and was caught by eye rather than by CI.

These run on a scratch database created for the session, so moving its
revision around cannot disturb the one the rest of the suite shares.
See tests/migration_fixtures.py.
"""

import pytest
from sqlalchemy import text

from tests.migration_fixtures import migrate, scratch_url        # noqa: F401


# The chain, oldest first.  Derived rather than hardcoded so a new revision
# is covered without editing this file.
def _revisions():
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from pathlib import Path

    cfg = Config(str(Path(__file__).resolve().parents[1] / "db" / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    return [r.revision for r in reversed(list(script.walk_revisions()))]


REVISIONS = _revisions()


# -----------------------------------------------------------------------------

def test_the_chain_is_discoverable() -> None:
    """Guards against _revisions() silently returning nothing."""
    assert len(REVISIONS) >= 6, REVISIONS
    assert REVISIONS[0] == "0001"


# -----------------------------------------------------------------------------

def test_full_chain_up_and_down(migrate) -> None:
    """base -> head -> base, so every downgrade is exercised at least once."""
    migrate.to("head")
    assert migrate.revision() == REVISIONS[-1]

    with migrate.session() as s:
        tables = s.execute(text(
            "SELECT count(*) FROM pg_tables WHERE schemaname='public'")).scalar()
    assert tables > 15

    migrate.to("base")
    with migrate.session() as s:
        left = s.execute(text(
            "SELECT count(*) FROM pg_tables WHERE schemaname='public'"
            " AND tablename <> 'alembic_version'")).scalar()
    assert left == 0, "downgrade left tables behind"


# -----------------------------------------------------------------------------

@pytest.mark.parametrize("index", range(1, len(REVISIONS)))
def test_each_revision_steps_back_and_forward(migrate, index) -> None:
    """Upgrade to a revision, step back exactly one, and come forward again.

    A downgrade that does not undo its own upgrade only shows up when someone
    needs to roll back, which is the worst moment to find out.  Stepping back
    one at a time isolates which revision is at fault; the full up-and-down
    test would only say that something in the chain was wrong.
    """
    revision, previous = REVISIONS[index], REVISIONS[index - 1]

    migrate.to(revision)
    assert migrate.revision() == revision

    migrate.to(previous)
    assert migrate.revision() == previous, f"{revision} did not downgrade to {previous}"

    migrate.to(revision)
    assert migrate.revision() == revision, f"{revision} did not re-apply after downgrade"


# -----------------------------------------------------------------------------

def test_0004_preserves_valid_self_references(migrate) -> None:
    """The regression that started this file.

    0004 adds the foreign keys, and first NULLs any reference that does not
    resolve.  For the four self-referencing columns its subquery was
    unaliased, so the inner FROM shadowed the outer table, every row looked
    dangling, and valid values were cleared.
    """
    migrate.to("0003")

    with migrate.session() as s:
        s.execute(text("INSERT INTO application_user (username) VALUES ('u1')"))
        s.execute(text("INSERT INTO user_role (name, parent_role_id) VALUES ('MD', NULL)"))
        s.execute(text("INSERT INTO user_role (name, parent_role_id) VALUES ('Sales', 1)"))
        s.execute(text("INSERT INTO account (name, parent_id) VALUES ('Parent', NULL)"))
        s.execute(text("INSERT INTO account (name, parent_id) VALUES ('Child', 1)"))
        s.execute(text("INSERT INTO contact (last_name, reports_to_id) VALUES ('Boss', NULL)"))
        s.execute(text("INSERT INTO contact (last_name, reports_to_id) VALUES ('Report', 1)"))
        s.commit()

    migrate.to("0004")

    with migrate.session() as s:
        assert s.execute(text(
            "SELECT parent_role_id FROM user_role WHERE name='Sales'")).scalar() == 1
        assert s.execute(text(
            "SELECT parent_id FROM account WHERE name='Child'")).scalar() == 1
        assert s.execute(text(
            "SELECT reports_to_id FROM contact WHERE last_name='Report'")).scalar() == 1


# -----------------------------------------------------------------------------

def test_0004_clears_genuinely_dangling_references(migrate) -> None:
    """The reconciliation must still do its job, or the constraint cannot apply."""
    migrate.to("0003")

    with migrate.session() as s:
        s.execute(text("INSERT INTO user_role (name, parent_role_id) VALUES ('Orphan', 999)"))
        s.execute(text("INSERT INTO application_user (username, delegated_approver_id)"
                       " VALUES ('sentinel', 0)"))
        s.commit()

    migrate.to("0004")

    with migrate.session() as s:
        assert s.execute(text(
            "SELECT parent_role_id FROM user_role WHERE name='Orphan'")).scalar() is None
        assert s.execute(text(
            "SELECT delegated_approver_id FROM application_user"
            " WHERE username='sentinel'")).scalar() is None


# -----------------------------------------------------------------------------

def test_0004_never_touches_a_primary_key(migrate) -> None:
    """An early draft of the reconciliation parsed the constraint names with a
    greedy regex and produced UPDATE ... SET id = NULL.  Rows surviving with
    their ids intact is the assertion that would have caught it."""
    migrate.to("0003")

    with migrate.session() as s:
        s.execute(text("INSERT INTO account (name) VALUES ('Keeps its id')"))
        s.commit()

    migrate.to("0004")

    with migrate.session() as s:
        assert s.execute(text(
            "SELECT id FROM account WHERE name='Keeps its id'")).scalar() == 1


# -----------------------------------------------------------------------------

def test_0005_indexes_every_foreign_key_column(migrate) -> None:
    migrate.to("0005")

    with migrate.session() as s:
        unindexed = s.execute(text("""
            SELECT count(*) FROM pg_constraint c
            JOIN unnest(c.conkey) k(attnum) ON true
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
            WHERE c.contype = 'f'
              AND NOT EXISTS (SELECT 1 FROM pg_index i
                              WHERE i.indrelid = c.conrelid AND a.attnum = i.indkey[0])
        """)).scalar()
    assert unindexed == 0


# -----------------------------------------------------------------------------

def test_0006_is_idempotent_and_respects_an_existing_row(migrate) -> None:
    """It must not overwrite what a deployment has already recorded."""
    migrate.to("0005")

    with migrate.session() as s:
        s.execute(text(
            "INSERT INTO instance_metadata (release, app_version, db_version, notes)"
            " VALUES ('prod', 'v9.9.9', 'v9.9.9', 'set by hand')"))
        s.commit()

    migrate.to("0006")

    with migrate.session() as s:
        rows = s.execute(text("SELECT count(*) FROM instance_metadata")).scalar()
        notes = s.execute(text("SELECT notes FROM instance_metadata")).scalar()
    assert rows == 1
    assert notes == "set by hand", "0006 overwrote an existing row"


# -----------------------------------------------------------------------------

def test_0006_stamps_a_row_when_there_is_none(migrate) -> None:
    migrate.to("0005")

    with migrate.session() as s:
        assert s.execute(text("SELECT count(*) FROM instance_metadata")).scalar() == 0

    migrate.to("0006")

    with migrate.session() as s:
        assert s.execute(text("SELECT count(*) FROM instance_metadata")).scalar() == 1


# -----------------------------------------------------------------------------

def test_data_survives_the_whole_chain(migrate) -> None:
    """Rows written at 0003 are still intact and correct at head."""
    migrate.to("0003")

    with migrate.session() as s:
        s.execute(text("INSERT INTO application_user (username, guid)"
                       " VALUES ('survivor', '11111111-1111-1111-1111-111111111111')"))
        s.execute(text("INSERT INTO account (name, owner_id) VALUES ('Acme', 1)"))
        s.execute(text("INSERT INTO contact (last_name, account_id, owner_id)"
                       " VALUES ('Nguyen', 1, 1)"))
        s.commit()

    migrate.to("head")

    with migrate.session() as s:
        assert s.execute(text("SELECT username FROM application_user")).scalar() == "survivor"
        assert s.execute(text("SELECT owner_id FROM account")).scalar() == 1
        assert s.execute(text(
            "SELECT account_id FROM contact")).scalar() == 1
        assert s.execute(text(
            "SELECT owner_id FROM contact")).scalar() == 1


# -----------------------------------------------------------------------------

def test_the_trigger_works_after_a_full_migration(migrate) -> None:
    """set_updated_at is created in 0001 and installed per table; a later
    migration must not leave it dangling."""
    migrate.to("head")

    with migrate.session() as s:
        s.execute(text("INSERT INTO account (name) VALUES ('Trigger test')"))
        s.commit()
        s.execute(text("UPDATE account SET updated_at = 'epoch'"))
        s.commit()
        stamped = s.execute(text("SELECT updated_at FROM account")).scalar()

    assert stamped.year > 2000, "the trigger did not overwrite the planted value"


# -----------------------------------------------------------------------------

def test_0007_adds_the_column_to_an_existing_table(migrate) -> None:
    """The column reaches a database that already holds users.

    db/schema/create/application_user.sql declares it too, so a fresh build
    arrives at 0007 with the work already done and the ALTER is a no-op.
    That is the path every other test takes; this one is the other path, and
    it is the only one that runs on a deployed database.
    """
    migrate.to("0006")

    with migrate.session() as s:
        s.execute(text("INSERT INTO application_user (username, guid)"
                       " VALUES ('predates', '22222222-2222-2222-2222-222222222222')"))
        s.commit()

    migrate.to("0007")

    with migrate.session() as s:
        assert s.execute(text("SELECT username FROM application_user")).scalar() == "predates"
        assert s.execute(text(
            "SELECT tokens_revoked_before FROM application_user")).scalar() is None, (
            "an existing user came out of the migration with tokens revoked")


# -----------------------------------------------------------------------------

def test_0007_survives_being_applied_twice(migrate) -> None:
    """ADD COLUMN IF NOT EXISTS, because the create script declares it too.

    A fresh build gets the column from 0001 and then runs this migration over
    the top of it.  Without IF NOT EXISTS that build fails outright, which is
    the same shape as the constraint duplication the create scripts avoid.
    """
    migrate.to("head")
    migrate.to("0006")
    migrate.to("head")

    with migrate.session() as s:
        assert s.execute(text(
            "SELECT count(*) FROM information_schema.columns"
            " WHERE table_name = 'application_user'"
            "   AND column_name = 'tokens_revoked_before'")).scalar() == 1


# -----------------------------------------------------------------------------

def test_0007_stamps_the_schema_version(migrate) -> None:
    """instance_metadata reports the release the schema last changed in.

    A migration that alters the schema without updating it leaves the
    endpoint describing an older database than the one it is talking to.
    """
    migrate.to("head")

    with migrate.session() as s:
        assert s.execute(text("SELECT db_version FROM instance_metadata")).scalar() == "v0.15.0"

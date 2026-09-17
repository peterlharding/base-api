"""Retention: three tables grow without bound, and they do not age alike.

    token_blacklist   by expiry - the row's purpose ends with the token
    login_session     by age, 90 days by default
    audit_log         by age, off by default

Covered in tests/test_blacklist_pruning.py for the first; this file is the
other two, and the policy that binds them.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, insert, select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import AuditLog, ApplicationUser, LoginSession


NOW = datetime.now(timezone.utc)


def _session_row(s, *, started, expires_at=None, revoked_at=None, user_id=1):
    """A session row.  The table enforces expires_at > started, so a session
    that has ended is one whose expiry is in the past - not one whose expiry
    equals its start."""
    s.execute(insert(LoginSession).values(
        session_token_hash=f"{started}{expires_at}{revoked_at}".encode()[:32],
        user_id=user_id, started=started,
        expires_at=expires_at if expires_at is not None
                   else started + timedelta(hours=1),
        revoked_at=revoked_at))


def _audit_row(s, *, created_at):
    s.execute(insert(AuditLog).values(
        application="test", action="create", reference_type="account",
        reference_id=1, description="", user_id="u", created_at=created_at))


@pytest.fixture()
def a_user(client):
    with SessionLocal() as s:
        s.execute(insert(ApplicationUser).values(username="retention", is_active=True))
        s.commit()
        return s.scalar(select(ApplicationUser.id))


# -----------------------------------------------------------------------------

def test_sessions_older_than_the_policy_are_removed(a_user) -> None:
    with SessionLocal() as s:
        _session_row(s, started=NOW - timedelta(days=200), user_id=a_user)
        _session_row(s, started=NOW - timedelta(days=91), user_id=a_user)
        _session_row(s, started=NOW - timedelta(days=10), user_id=a_user)
        s.commit()

        removed = LoginSession.prune_older_than(s, 90, now=NOW)
        s.commit()

        assert removed == 2
        assert s.scalar(select(func.count()).select_from(LoginSession)) == 1


# -----------------------------------------------------------------------------

def test_a_session_that_has_not_ended_is_never_removed(a_user) -> None:
    """However old it is: deleting the record of a session that still works
    would leave the API unable to say who is connected."""
    with SessionLocal() as s:
        _session_row(s, started=NOW - timedelta(days=500),
                     expires_at=NOW + timedelta(hours=1), user_id=a_user)
        s.commit()

        assert LoginSession.prune_older_than(s, 90, now=NOW) == 0
        s.commit()
        assert s.scalar(select(func.count()).select_from(LoginSession)) == 1


# -----------------------------------------------------------------------------

def test_a_revoked_session_is_removable_even_though_it_has_not_expired(a_user) -> None:
    with SessionLocal() as s:
        _session_row(s, started=NOW - timedelta(days=200),
                     expires_at=NOW + timedelta(hours=1),
                     revoked_at=NOW - timedelta(days=200), user_id=a_user)
        s.commit()

        assert LoginSession.prune_older_than(s, 90, now=NOW) == 1
        s.commit()


# -----------------------------------------------------------------------------

def test_zero_days_keeps_sessions_indefinitely(a_user) -> None:
    with SessionLocal() as s:
        _session_row(s, started=NOW - timedelta(days=5000), user_id=a_user)
        s.commit()

        assert LoginSession.prune_older_than(s, 0, now=NOW) == 0
        s.commit()
        assert s.scalar(select(func.count()).select_from(LoginSession)) == 1


# -----------------------------------------------------------------------------

def test_audit_entries_are_kept_indefinitely_by_default(client) -> None:
    """The default is 0, and 0 deletes nothing however old the row."""
    assert get_settings().audit_log_retention_days == 0

    with SessionLocal() as s:
        _audit_row(s, created_at=NOW - timedelta(days=5000))
        s.commit()

        assert AuditLog.prune_older_than(
            s, get_settings().audit_log_retention_days, now=NOW) == 0
        s.commit()
        assert s.scalar(select(func.count()).select_from(AuditLog)) == 1


# -----------------------------------------------------------------------------

def test_audit_entries_can_be_pruned_when_a_policy_is_set(client) -> None:
    """The mechanism is present so tightening it is a settings change."""
    with SessionLocal() as s:
        _audit_row(s, created_at=NOW - timedelta(days=400))
        _audit_row(s, created_at=NOW - timedelta(days=10))
        s.commit()

        assert AuditLog.prune_older_than(s, 365, now=NOW) == 1
        s.commit()
        assert s.scalar(select(func.count()).select_from(AuditLog)) == 1


# -----------------------------------------------------------------------------

def test_the_boundary_is_strictly_older(client) -> None:
    """A row exactly at the cutoff survives.  Arbitrary, but decided."""
    with SessionLocal() as s:
        cutoff = NOW - timedelta(days=90)
        _audit_row(s, created_at=cutoff)
        _audit_row(s, created_at=cutoff - timedelta(microseconds=1))
        s.commit()

        assert AuditLog.prune_older_than(s, 90, now=NOW) == 1
        s.commit()
        assert s.scalar(select(func.count()).select_from(AuditLog)) == 1


# -----------------------------------------------------------------------------

def test_pruning_sessions_does_not_touch_the_audit_trail(a_user) -> None:
    """Each table has its own policy; one must not take the other with it."""
    with SessionLocal() as s:
        _session_row(s, started=NOW - timedelta(days=200), user_id=a_user)
        _audit_row(s, created_at=NOW - timedelta(days=200))
        s.commit()

        LoginSession.prune_older_than(s, 90, now=NOW)
        s.commit()

        assert s.scalar(select(func.count()).select_from(LoginSession)) == 0
        assert s.scalar(select(func.count()).select_from(AuditLog)) == 1


# -----------------------------------------------------------------------------

def test_pruning_is_idempotent(a_user) -> None:
    with SessionLocal() as s:
        _session_row(s, started=NOW - timedelta(days=200), user_id=a_user)
        s.commit()

        assert LoginSession.prune_older_than(s, 90, now=NOW) == 1
        s.commit()
        assert LoginSession.prune_older_than(s, 90, now=NOW) == 0
        s.commit()

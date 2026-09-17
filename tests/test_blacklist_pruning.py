"""token_blacklist only grows on logout, and must not grow forever.

A blacklist row only has to outlive the token it revokes: once the expiry
has passed, the token fails validation on its own and the row is answering a
question nobody will ask.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, insert, select

from app.db.session import SessionLocal
from app.models import ApplicationUser, TokenBlacklist


def _row(session, *, expiry, user_id=None):
    session.execute(insert(TokenBlacklist).values(
        jti=uuid4(), user_id=user_id, reason="test", expiry=expiry))


@pytest.fixture()
def blacklist(client):
    """Three rows: two long expired, one still live."""
    now = datetime.now(timezone.utc)
    with SessionLocal() as s:
        _row(s, expiry=now - timedelta(hours=2))
        _row(s, expiry=now - timedelta(minutes=1))
        _row(s, expiry=now + timedelta(hours=1))
        s.commit()
    return now


# -----------------------------------------------------------------------------

def test_prunes_only_expired_rows(blacklist) -> None:
    with SessionLocal() as s:
        assert s.scalar(select(func.count()).select_from(TokenBlacklist)) == 3

        pruned = TokenBlacklist.prune_expired(s)
        s.commit()

        assert pruned == 2
        remaining = s.scalars(select(TokenBlacklist.expiry)).all()
        assert len(remaining) == 1
        assert remaining[0] > blacklist, "a live revocation was deleted"


# -----------------------------------------------------------------------------

def test_is_idempotent(blacklist) -> None:
    with SessionLocal() as s:
        TokenBlacklist.prune_expired(s)
        s.commit()
        assert TokenBlacklist.prune_expired(s) == 0
        s.commit()


# -----------------------------------------------------------------------------

def test_prunes_nothing_when_all_rows_are_live(client) -> None:
    now = datetime.now(timezone.utc)
    with SessionLocal() as s:
        _row(s, expiry=now + timedelta(hours=1))
        s.commit()
        assert TokenBlacklist.prune_expired(s) == 0
        s.commit()
        assert s.scalar(select(func.count()).select_from(TokenBlacklist)) == 1


# -----------------------------------------------------------------------------

def test_a_row_expiring_exactly_now_is_pruned(client) -> None:
    """The boundary: expiry < cutoff, so a row at the cutoff survives."""
    cutoff = datetime.now(timezone.utc)
    with SessionLocal() as s:
        _row(s, expiry=cutoff - timedelta(microseconds=1))
        _row(s, expiry=cutoff)
        s.commit()

        assert TokenBlacklist.prune_expired(s, now=cutoff) == 1
        s.commit()
        assert s.scalar(select(func.count()).select_from(TokenBlacklist)) == 1


# -----------------------------------------------------------------------------

def test_logout_prunes_but_keeps_its_own_row(protected_client) -> None:
    """The row logout has just written must survive its own pruning pass."""
    import base64

    from app.auth.password import hash_password
    from app.models import ApiCredential

    with SessionLocal() as s:
        s.execute(insert(ApiCredential).values(
            email="prune@example.com", hashed_password=hash_password("pw")))
        s.execute(insert(ApplicationUser).values(
            username="pruner", guid="0b0b0b0b-1111-2222-3333-444444444444",
            is_active=True, hashed_password=hash_password("upw")))
        # an already-dead revocation from some earlier session
        _row(s, expiry=datetime.now(timezone.utc) - timedelta(hours=2))
        s.commit()

    basic = base64.b64encode(b"prune@example.com:pw").decode()
    token = protected_client.post(
        "/api/v1/auth/authenticate",
        json={"username": "pruner", "password": "upw"},
        headers={"Authorization": f"Basic {basic}"}).json()["token"]

    assert protected_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}).status_code == 204

    with SessionLocal() as s:
        rows = s.scalars(select(TokenBlacklist)).all()

    assert len(rows) == 1, "logout should have pruned the stale row and kept its own"
    assert rows[0].reason == "logout"

    # and the token it just revoked is still refused
    assert protected_client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"}).status_code == 401


# -----------------------------------------------------------------------------

def test_pruning_does_not_unrevoke_a_live_token(protected_client) -> None:
    """The obvious way to get this wrong is to delete too much."""
    import base64

    from app.auth.password import hash_password
    from app.models import ApiCredential

    with SessionLocal() as s:
        s.execute(insert(ApiCredential).values(
            email="live@example.com", hashed_password=hash_password("pw")))
        s.execute(insert(ApplicationUser).values(
            username="liveuser", guid="0c0c0c0c-1111-2222-3333-444444444444",
            is_active=True, hashed_password=hash_password("upw")))
        s.commit()

    basic = base64.b64encode(b"live@example.com:pw").decode()

    def sign_in():
        return protected_client.post(
            "/api/v1/auth/authenticate",
            json={"username": "liveuser", "password": "upw"},
            headers={"Authorization": f"Basic {basic}"}).json()["token"]

    revoked, other = sign_in(), sign_in()
    protected_client.post("/api/v1/auth/logout",
                          headers={"Authorization": f"Bearer {revoked}"})

    with SessionLocal() as s:
        TokenBlacklist.prune_expired(s)
        s.commit()

    assert protected_client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {revoked}"}).status_code == 401, \
        "pruning resurrected a revoked token"
    assert protected_client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {other}"}).status_code == 200

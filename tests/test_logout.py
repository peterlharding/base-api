"""POST /api/v1/auth/logout - revoke the token this request was made with.

Revocation has to be real: the jti goes into token_blacklist, which the
bearer dependency checks on every request, so the token stops working rather
than merely being dropped by the client.
"""

import base64
import hashlib

import pytest
from sqlalchemy import insert, select

from app.auth.password import hash_password
from app.db.session import SessionLocal
from app.models import ApiCredential, ApplicationUser, LoginSession, TokenBlacklist


CLIENT, SECRET = "logout@example.com", "client-pw"
USER, USER_PW = "logout-user", "user-pw"
GUID = "cafecafe-1111-2222-3333-444444444444"


def _basic():
    raw = base64.b64encode(f"{CLIENT}:{SECRET}".encode()).decode()
    return {"Authorization": f"Basic {raw}"}


@pytest.fixture()
def signed_in(protected_client):
    """A real sign-in, returning the token it issued."""
    with SessionLocal() as s:
        s.execute(insert(ApiCredential).values(
            email=CLIENT, hashed_password=hash_password(SECRET)))
        s.execute(insert(ApplicationUser).values(
            username=USER, guid=GUID, is_active=True,
            hashed_password=hash_password(USER_PW)))
        s.commit()

    r = protected_client.post("/api/v1/auth/authenticate",
                              json={"username": USER, "password": USER_PW},
                              headers=_basic())
    assert r.status_code == 200
    return r.json()["token"]


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


# -----------------------------------------------------------------------------

def test_logout_returns_204(protected_client, signed_in) -> None:
    r = protected_client.post("/api/v1/auth/logout", headers=_bearer(signed_in))
    assert r.status_code == 204


# -----------------------------------------------------------------------------

def test_the_token_stops_working(protected_client, signed_in) -> None:
    """The point of the endpoint: revoked means revoked, server-side."""
    assert protected_client.get("/api/v1/users",
                                headers=_bearer(signed_in)).status_code == 200

    protected_client.post("/api/v1/auth/logout", headers=_bearer(signed_in))

    r = protected_client.get("/api/v1/users", headers=_bearer(signed_in))
    assert r.status_code == 401
    assert r.json()["detail"] == "Token has been revoked"


# -----------------------------------------------------------------------------

def test_a_revoked_token_cannot_be_refreshed(protected_client, signed_in) -> None:
    """Otherwise logging out achieves nothing - refresh would mint a new one.

    refresh does not go through the bearer dependency, so it checks the
    blacklist itself.
    """
    protected_client.post("/api/v1/auth/logout", headers=_bearer(signed_in))

    r = protected_client.post("/api/v1/auth/refresh", headers=_bearer(signed_in))
    assert r.status_code == 401
    assert r.json()["detail"] == "Token has been revoked"


# -----------------------------------------------------------------------------

def test_the_session_is_stamped_revoked(protected_client, signed_in) -> None:
    with SessionLocal() as s:
        assert s.scalar(select(LoginSession.revoked_at)) is None

    protected_client.post("/api/v1/auth/logout", headers=_bearer(signed_in))

    with SessionLocal() as s:
        assert s.scalar(select(LoginSession.revoked_at)) is not None


# -----------------------------------------------------------------------------

def test_the_session_drops_out_of_the_active_filter(protected_client, signed_in) -> None:
    assert len(protected_client.get("/api/v1/login-sessions",
                                    params={"active": True},
                                    headers=_bearer(signed_in)).json()) == 1

    protected_client.post("/api/v1/auth/logout", headers=_bearer(signed_in))

    # a second sign-in, since the first token no longer works
    fresh = protected_client.post("/api/v1/auth/authenticate",
                                  json={"username": USER, "password": USER_PW},
                                  headers=_basic()).json()["token"]

    active = protected_client.get("/api/v1/login-sessions",
                                  params={"active": True},
                                  headers=_bearer(fresh)).json()
    assert len(active) == 1, "the revoked session is still counted as active"


# -----------------------------------------------------------------------------

def test_the_blacklist_row_records_who_and_when(protected_client, signed_in) -> None:
    protected_client.post("/api/v1/auth/logout", headers=_bearer(signed_in))

    with SessionLocal() as s:
        row = s.scalar(select(TokenBlacklist))
        user = s.scalar(select(ApplicationUser).where(ApplicationUser.guid == GUID))
        assert row is not None
        assert row.user_id == user.id
        assert row.reason == "logout"
        assert row.expiry is not None, "without an expiry the row can never be pruned"


# -----------------------------------------------------------------------------

def test_a_second_logout_is_rejected(protected_client, signed_in) -> None:
    """Not an error path so much as proof the first one took effect."""
    assert protected_client.post("/api/v1/auth/logout",
                                 headers=_bearer(signed_in)).status_code == 204

    r = protected_client.post("/api/v1/auth/logout", headers=_bearer(signed_in))
    assert r.status_code == 401


# -----------------------------------------------------------------------------

def test_other_tokens_for_the_same_user_keep_working(protected_client, signed_in) -> None:
    """Signing out on one device must not sign the user out everywhere."""
    second = protected_client.post("/api/v1/auth/authenticate",
                                   json={"username": USER, "password": USER_PW},
                                   headers=_basic()).json()["token"]

    protected_client.post("/api/v1/auth/logout", headers=_bearer(signed_in))

    assert protected_client.get("/api/v1/users",
                                headers=_bearer(signed_in)).status_code == 401
    assert protected_client.get("/api/v1/users",
                                headers=_bearer(second)).status_code == 200


# -----------------------------------------------------------------------------

def test_logout_requires_a_token(protected_client) -> None:
    assert protected_client.post("/api/v1/auth/logout").status_code in (401, 403)


# -----------------------------------------------------------------------------

def test_each_token_has_its_own_jti(protected_client, signed_in) -> None:
    """Revoking one must be able to leave the other alone."""
    from app.auth.handler import decode_token

    second = protected_client.post("/api/v1/auth/authenticate",
                                   json={"username": USER, "password": USER_PW},
                                   headers=_basic()).json()["token"]

    assert decode_token(signed_in)["jti"] != decode_token(second)["jti"]

"""POST /api/v1/auth/revoke-all - revoke every token the caller holds.

Where logout revokes the one token the request was made with, this revokes
all of them.  The mechanism is a cutoff on application_user rather than more
token_blacklist rows, because the blacklist is keyed on jti and nothing
holds a list of a user's outstanding jtis: login_session stores a hash of
the token rather than its id, and a token obtained from refresh creates no
session row at all.  The tests below pin exactly that - a token the database
has no record of still has to stop working.
"""

import base64

from datetime import datetime, timedelta, timezone

import pytest

from sqlalchemy import func, insert, select

from app.auth.handler import decode_token
from app.auth.password import hash_password
from app.db.session import SessionLocal
from app.models import ApiCredential, ApplicationUser, LoginSession, TokenBlacklist


CLIENT, SECRET = "revoke@example.com", "client-pw"
USER, USER_PW = "revoke-user", "user-pw"
GUID = "beefbeef-1111-2222-3333-555555555555"

OTHER, OTHER_PW = "bystander", "other-pw"
OTHER_GUID = "beefbeef-1111-2222-3333-666666666666"


def _basic():
    raw = base64.b64encode(f"{CLIENT}:{SECRET}".encode()).decode()
    return {"Authorization": f"Basic {raw}"}


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def accounts():
    """The API client and two users, so "everywhere" can be bounded."""
    with SessionLocal() as s:
        s.execute(insert(ApiCredential).values(
            email=CLIENT, hashed_password=hash_password(SECRET)))
        s.execute(insert(ApplicationUser).values(
            username=USER, guid=GUID, is_active=True,
            hashed_password=hash_password(USER_PW)))
        s.execute(insert(ApplicationUser).values(
            username=OTHER, guid=OTHER_GUID, is_active=True,
            hashed_password=hash_password(OTHER_PW)))
        s.commit()


@pytest.fixture()
def sign_in(protected_client, accounts):
    """Sign in as either user, returning the token.  Call it repeatedly."""
    def _sign_in(username=USER, password=USER_PW):
        r = protected_client.post("/api/v1/auth/authenticate",
                                  json={"username": username, "password": password},
                                  headers=_basic())
        assert r.status_code == 200
        return r.json()["token"]

    return _sign_in


# -----------------------------------------------------------------------------

def test_revoke_all_reports_what_it_did(protected_client, sign_in) -> None:
    token = sign_in()

    r = protected_client.post("/api/v1/auth/revoke-all", headers=_bearer(token))

    assert r.status_code == 200
    assert r.json()["sessions_ended"] == 1
    assert r.json()["revoked_before"] is not None


# -----------------------------------------------------------------------------

def test_every_token_for_the_user_stops_working(protected_client, sign_in) -> None:
    """The point of the endpoint, and what logout deliberately does not do."""
    first, second, third = sign_in(), sign_in(), sign_in()

    assert protected_client.get("/api/v1/users", headers=_bearer(second)).status_code == 200

    protected_client.post("/api/v1/auth/revoke-all", headers=_bearer(first))

    for token in (first, second, third):
        r = protected_client.get("/api/v1/users", headers=_bearer(token))
        assert r.status_code == 401
        assert r.json()["detail"] == "Token has been revoked"


# -----------------------------------------------------------------------------

def test_a_refreshed_token_stops_working(protected_client, sign_in) -> None:
    """The case a jti blacklist could not reach.

    refresh mints a token without writing a login_session row, so nothing in
    the database records that it exists.  A cutoff does not need to know.
    """
    original = sign_in()

    refreshed = protected_client.post("/api/v1/auth/refresh",
                                      headers=_bearer(original)).json()["token"]
    assert protected_client.get("/api/v1/users",
                                headers=_bearer(refreshed)).status_code == 200

    protected_client.post("/api/v1/auth/revoke-all", headers=_bearer(original))

    assert protected_client.get("/api/v1/users",
                                headers=_bearer(refreshed)).status_code == 401


# -----------------------------------------------------------------------------

def test_the_callers_own_token_stops_working(protected_client, sign_in) -> None:
    """Revoke all means all.  Sparing the current device would be a carve-out."""
    token = sign_in()

    assert protected_client.post("/api/v1/auth/revoke-all",
                                 headers=_bearer(token)).status_code == 200

    assert protected_client.get("/api/v1/users", headers=_bearer(token)).status_code == 401


# -----------------------------------------------------------------------------

def test_a_revoked_token_cannot_be_refreshed(protected_client, sign_in) -> None:
    """refresh does not go through the bearer dependency, so it checks too.

    Without this the endpoint would achieve nothing: any revoked token could
    be walked straight back into a working one.
    """
    token = sign_in()

    protected_client.post("/api/v1/auth/revoke-all", headers=_bearer(token))

    r = protected_client.post("/api/v1/auth/refresh", headers=_bearer(token))
    assert r.status_code == 401
    assert r.json()["detail"] == "Token has been revoked"


# -----------------------------------------------------------------------------

def test_signing_in_again_works(protected_client, sign_in) -> None:
    """The cutoff is an instant, not a lock: it must not bar the next token."""
    protected_client.post("/api/v1/auth/revoke-all", headers=_bearer(sign_in()))

    assert protected_client.get("/api/v1/users",
                                headers=_bearer(sign_in())).status_code == 200


# -----------------------------------------------------------------------------

def test_another_users_tokens_are_untouched(protected_client, sign_in) -> None:
    mine, theirs = sign_in(), sign_in(OTHER, OTHER_PW)

    protected_client.post("/api/v1/auth/revoke-all", headers=_bearer(mine))

    assert protected_client.get("/api/v1/users", headers=_bearer(mine)).status_code == 401
    assert protected_client.get("/api/v1/users", headers=_bearer(theirs)).status_code == 200


# -----------------------------------------------------------------------------

def test_the_sessions_are_stamped_revoked(protected_client, sign_in) -> None:
    token = sign_in()
    sign_in()

    protected_client.post("/api/v1/auth/revoke-all", headers=_bearer(token))

    with SessionLocal() as s:
        open_sessions = s.scalar(
            select(func.count()).select_from(LoginSession)
            .where(LoginSession.revoked_at.is_(None))
        )
        assert open_sessions == 0, "a session outlived the token that created it"


# -----------------------------------------------------------------------------

def test_an_already_revoked_session_keeps_its_timestamp(protected_client, sign_in) -> None:
    """Logout recorded when that session ended; revoke-all must not rewrite it."""
    first, second = sign_in(), sign_in()

    protected_client.post("/api/v1/auth/logout", headers=_bearer(first))

    with SessionLocal() as s:
        at_logout = s.scalar(
            select(LoginSession.revoked_at).where(LoginSession.revoked_at.is_not(None))
        )

    r = protected_client.post("/api/v1/auth/revoke-all", headers=_bearer(second))
    assert r.json()["sessions_ended"] == 1, "the logged-out session was counted again"

    with SessionLocal() as s:
        stamps = set(s.scalars(select(LoginSession.revoked_at)))

    assert at_logout in stamps


# -----------------------------------------------------------------------------

def test_no_blacklist_rows_are_added(protected_client, sign_in) -> None:
    """A row per outstanding token is the design this replaces.

    Two of the three tokens here are not in any table the API could consult,
    which is the whole reason the blacklist cannot do this job.
    """
    token = sign_in()
    sign_in()
    sign_in()

    protected_client.post("/api/v1/auth/revoke-all", headers=_bearer(token))

    with SessionLocal() as s:
        assert s.scalar(select(func.count()).select_from(TokenBlacklist)) == 0


# -----------------------------------------------------------------------------

def test_revoke_all_requires_a_token(protected_client) -> None:
    assert protected_client.post("/api/v1/auth/revoke-all").status_code in (401, 403)


# -----------------------------------------------------------------------------
# The cutoff itself.  Tokens are issued and revoked within the same second in
# every test above, so the comparison has to be finer than a second or the
# outcome depends on where the truncation falls.

def test_tokens_carry_a_fractional_issued_at(protected_client, sign_in) -> None:
    issued = [decode_token(sign_in())["iat"] for _ in range(8)]

    assert any(value % 1 for value in issued), (
        "iat is whole seconds, so a token minted in the same second as a "
        "revoke-all cannot be placed either side of it"
    )


# -----------------------------------------------------------------------------

def test_the_cutoff_is_compared_below_the_second() -> None:
    cutoff = datetime(2026, 9, 18, 12, 0, 0, 500_000, tzinfo=timezone.utc)
    user = ApplicationUser(tokens_revoked_before=cutoff)

    assert user.rejects_token_issued_at((cutoff - timedelta(milliseconds=1)).timestamp())
    assert not user.rejects_token_issued_at((cutoff + timedelta(milliseconds=1)).timestamp())


# -----------------------------------------------------------------------------

def test_nothing_is_revoked_until_the_endpoint_is_used() -> None:
    user = ApplicationUser()

    assert user.tokens_revoked_before is None
    assert not user.rejects_token_issued_at(datetime(1970, 1, 1, tzinfo=timezone.utc).timestamp())


# -----------------------------------------------------------------------------

def test_a_token_with_no_issued_at_is_refused_once_a_cutoff_exists() -> None:
    """Fail closed: with no iat there is no way to place the token."""
    user = ApplicationUser()

    assert not user.rejects_token_issued_at(None)

    user.revoke_tokens()

    assert user.rejects_token_issued_at(None)

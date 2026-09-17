"""/api/v1/login-sessions - read-only; the API writes these rows itself."""

import base64
import hashlib

from sqlalchemy import insert, select

from app.auth.password import hash_password
from app.db.session import SessionLocal
from app.models import ApiCredential, ApplicationUser, LoginSession


CLIENT, SECRET = "sessions@example.com", "client-pw"
USER, USER_PW = "session-user", "user-pw"
GUID = "77777777-8888-9999-aaaa-bbbbbbbbbbbb"


def _basic():
    raw = base64.b64encode(f"{CLIENT}:{SECRET}".encode()).decode()
    return {"Authorization": f"Basic {raw}"}


def _sign_in(client):
    with SessionLocal() as s:
        if not s.scalar(select(ApiCredential).where(ApiCredential.email == CLIENT)):
            s.execute(insert(ApiCredential).values(
                email=CLIENT, hashed_password=hash_password(SECRET)))
        if not s.scalar(select(ApplicationUser).where(ApplicationUser.username == USER)):
            s.execute(insert(ApplicationUser).values(
                username=USER, guid=GUID, is_active=True,
                hashed_password=hash_password(USER_PW)))
        s.commit()

    return client.post("/api/v1/auth/authenticate",
                       json={"username": USER, "password": USER_PW},
                       headers=_basic())


# -----------------------------------------------------------------------------

def test_authenticating_records_a_session(client) -> None:
    assert client.get("/api/v1/login-sessions").json() == []

    assert _sign_in(client).status_code == 200

    sessions = client.get("/api/v1/login-sessions").json()
    assert len(sessions) == 1
    assert sessions[0]["user_id"] is not None


# -----------------------------------------------------------------------------

def test_the_token_itself_is_never_stored_or_returned(client) -> None:
    """Only a SHA-256 of it, and the endpoint does not expose even that."""
    token = _sign_in(client).json()["token"]

    body = client.get("/api/v1/login-sessions").json()[0]
    assert "session_token_hash" not in body

    with SessionLocal() as s:
        stored = s.scalar(select(LoginSession.session_token_hash))
    assert stored == hashlib.sha256(token.encode()).digest()
    assert token.encode() not in stored


# -----------------------------------------------------------------------------

def test_records_the_client_host(client) -> None:
    """ip_address is INET, so a non-address host goes to workstation instead.

    TestClient reports the literal "testclient", which is exactly the case
    that used to fail the insert and lose the sign-in silently.
    """
    _sign_in(client)
    body = client.get("/api/v1/login-sessions").json()[0]
    assert (body["ip_address"] or body["workstation"]) is not None
    assert body["started"] is not None
    assert body["expires_at"] is not None


# -----------------------------------------------------------------------------

def test_refresh_advances_last_seen(client) -> None:
    token = _sign_in(client).json()["token"]
    before = client.get("/api/v1/login-sessions").json()[0]["last_seen"]

    r = client.post("/api/v1/auth/refresh",
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200

    after = client.get("/api/v1/login-sessions").json()[0]["last_seen"]
    assert after >= before


# -----------------------------------------------------------------------------

def test_filter_by_user(client) -> None:
    _sign_in(client)
    body = client.get("/api/v1/login-sessions").json()[0]

    assert len(client.get("/api/v1/login-sessions",
                          params={"user_id": body["user_id"]}).json()) == 1
    assert client.get("/api/v1/login-sessions",
                      params={"user_id": 999999}).json() == []


# -----------------------------------------------------------------------------

def test_filter_by_active(client) -> None:
    _sign_in(client)
    assert len(client.get("/api/v1/login-sessions", params={"active": True}).json()) == 1
    assert client.get("/api/v1/login-sessions", params={"active": False}).json() == []


# -----------------------------------------------------------------------------

def test_get_by_id_and_404(client) -> None:
    _sign_in(client)
    body = client.get("/api/v1/login-sessions").json()[0]
    assert client.get(f"/api/v1/login-sessions/{body['id']}").status_code == 200

    r = client.get("/api/v1/login-sessions/999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Login session 999999 not found"


# -----------------------------------------------------------------------------

def test_a_real_ip_serialises(client) -> None:
    """ip_address is INET, which comes back as an address object not a str.

    TestClient reports "testclient", which lands in workstation and leaves
    this column NULL - so the sign-in path alone never exercises it, and a
    wrongly typed schema would only fail against a real client.
    """
    _sign_in(client)
    with SessionLocal() as s:
        s.execute(LoginSession.__table__.update().values(ip_address="203.0.113.7"))
        s.commit()

    r = client.get("/api/v1/login-sessions")
    assert r.status_code == 200, r.text
    assert r.json()[0]["ip_address"] == "203.0.113.7"


# -----------------------------------------------------------------------------

def test_is_read_only(client) -> None:
    """No POST, PUT or DELETE: a client cannot forge or erase a sign-in."""
    _sign_in(client)
    sid = client.get("/api/v1/login-sessions").json()[0]["id"]

    assert client.post("/api/v1/login-sessions", json={}).status_code == 405
    for method in ("put", "delete", "patch"):
        r = getattr(client, method)(f"/api/v1/login-sessions/{sid}")
        assert r.status_code == 405, f"{method.upper()} is accepted"


# -----------------------------------------------------------------------------

def test_a_failed_sign_in_records_nothing(client) -> None:
    _sign_in(client)                                    # create the fixtures
    with SessionLocal() as s:
        s.execute(LoginSession.__table__.delete())
        s.commit()

    client.post("/api/v1/auth/authenticate",
                json={"username": USER, "password": "wrong"}, headers=_basic())

    assert client.get("/api/v1/login-sessions").json() == []

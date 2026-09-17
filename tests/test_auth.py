"""End-to-end tests for /api/v1/auth.

Two layers must pass before a token is issued: HTTP Basic against
api_credentials, then the JSON body against application_user.

Note that api_credentials is seeded by migration 0002, so it survives the
per-test TRUNCATE only if it is in Base.metadata - it is, and the fixture
clears it, so these tests create the client credential they need.
"""

import base64
from datetime import timedelta

import jwt
import pytest

from app.auth.handler import decode_token, sign_token
from app.auth.password import hash_password


CLIENT_EMAIL = "client@example.com"
CLIENT_SECRET = "client-secret"
USER_NAME = "alice"
USER_PASSWORD = "user-password"


# -----------------------------------------------------------------------------

def _basic(username: str, password: str) -> dict:
    raw = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {raw}"}


@pytest.fixture()
def client_credential(client):
    """A row in api_credentials for the Basic Auth layer."""
    from sqlalchemy import insert
    from app.db.session import SessionLocal
    from app.models import ApiCredential

    with SessionLocal() as s:
        s.execute(insert(ApiCredential).values(
            email=CLIENT_EMAIL, hashed_password=hash_password(CLIENT_SECRET)))
        s.commit()


@pytest.fixture()
def user(client):
    """An application_user with a known bcrypt password."""
    from sqlalchemy import update
    from app.db.session import SessionLocal
    from app.models import ApplicationUser

    created = client.post("/api/v1/users", json={
        "username": USER_NAME,
        "guid": "11111111-2222-3333-4444-555555555555",
    }).json()

    with SessionLocal() as s:
        s.execute(update(ApplicationUser)
                  .where(ApplicationUser.id == created["id"])
                  .values(hashed_password=hash_password(USER_PASSWORD)))
        s.commit()
    return created


# -----------------------------------------------------------------------------

def test_authenticate_issues_a_token(client, client_credential, user) -> None:
    r = client.post(
        "/api/v1/auth/authenticate",
        json={"username": USER_NAME, "password": USER_PASSWORD},
        headers=_basic(CLIENT_EMAIL, CLIENT_SECRET),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["refresh_interval"] == 3600
    assert body["user"]["username"] == USER_NAME
    assert decode_token(body["token"])["sub"] == user["guid"]


# -----------------------------------------------------------------------------

def test_token_never_carries_the_password(client, client_credential, user) -> None:
    r = client.post(
        "/api/v1/auth/authenticate",
        json={"username": USER_NAME, "password": USER_PASSWORD},
        headers=_basic(CLIENT_EMAIL, CLIENT_SECRET),
    )
    assert "hashed_password" not in r.json()["user"]
    assert "password" not in r.json()["user"]


# -----------------------------------------------------------------------------

def test_basic_auth_is_required(client, client_credential, user) -> None:
    """Correct user credentials alone are not enough."""
    r = client.post(
        "/api/v1/auth/authenticate",
        json={"username": USER_NAME, "password": USER_PASSWORD},
    )
    assert r.status_code == 401


# -----------------------------------------------------------------------------

def test_wrong_client_secret_is_rejected(client, client_credential, user) -> None:
    r = client.post(
        "/api/v1/auth/authenticate",
        json={"username": USER_NAME, "password": USER_PASSWORD},
        headers=_basic(CLIENT_EMAIL, "wrong"),
    )
    assert r.status_code == 401


# -----------------------------------------------------------------------------

def test_wrong_user_password_is_rejected(client, client_credential, user) -> None:
    r = client.post(
        "/api/v1/auth/authenticate",
        json={"username": USER_NAME, "password": "wrong"},
        headers=_basic(CLIENT_EMAIL, CLIENT_SECRET),
    )
    assert r.status_code == 401


# -----------------------------------------------------------------------------

def test_unknown_user_and_wrong_password_are_indistinguishable(
    client, client_credential, user
) -> None:
    """Otherwise the endpoint enumerates valid usernames."""
    unknown = client.post(
        "/api/v1/auth/authenticate",
        json={"username": "nobody", "password": USER_PASSWORD},
        headers=_basic(CLIENT_EMAIL, CLIENT_SECRET),
    )
    wrong = client.post(
        "/api/v1/auth/authenticate",
        json={"username": USER_NAME, "password": "wrong"},
        headers=_basic(CLIENT_EMAIL, CLIENT_SECRET),
    )
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


# -----------------------------------------------------------------------------

def test_inactive_user_is_rejected(client, client_credential, user) -> None:
    client.put(f"/api/v1/users/{user['id']}", json={"is_active": False})
    r = client.post(
        "/api/v1/auth/authenticate",
        json={"username": USER_NAME, "password": USER_PASSWORD},
        headers=_basic(CLIENT_EMAIL, CLIENT_SECRET),
    )
    assert r.status_code == 401


# -----------------------------------------------------------------------------

def test_authenticate_stamps_last_login(client, client_credential, user) -> None:
    assert user["last_login_date"] is None
    r = client.post(
        "/api/v1/auth/authenticate",
        json={"username": USER_NAME, "password": USER_PASSWORD},
        headers=_basic(CLIENT_EMAIL, CLIENT_SECRET),
    )
    assert r.json()["user"]["last_login_date"] is not None


# -----------------------------------------------------------------------------

def test_refresh_returns_a_new_token(client, client_credential, user) -> None:
    token = sign_token(user["guid"])
    r = client.post("/api/v1/auth/refresh",
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert decode_token(r.json()["token"])["sub"] == user["guid"]


# -----------------------------------------------------------------------------

def test_refresh_accepts_a_recently_expired_token(client, client_credential, user) -> None:
    token = sign_token(user["guid"], ttl=timedelta(minutes=-5))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)

    r = client.post("/api/v1/auth/refresh",
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, "a recently expired token must still refresh"


# -----------------------------------------------------------------------------

def test_refresh_rejects_a_long_expired_token(client, client_credential, user) -> None:
    token = sign_token(user["guid"], ttl=timedelta(hours=-25))
    r = client.post("/api/v1/auth/refresh",
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert "too old" in r.json()["detail"]


# -----------------------------------------------------------------------------

def test_refresh_rejects_a_forged_token(client, client_credential, user) -> None:
    """Expiry is waived; the signature never is."""
    forged = jwt.encode({"sub": user["guid"], "exp": 9999999999},
                        "not-the-real-secret", algorithm="HS256")
    r = client.post("/api/v1/auth/refresh",
                    headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


# -----------------------------------------------------------------------------

def test_refresh_requires_a_bearer_header(client) -> None:
    assert client.post("/api/v1/auth/refresh").status_code == 401
    assert client.post("/api/v1/auth/refresh",
                       headers={"Authorization": "Basic abc"}).status_code == 401


# -----------------------------------------------------------------------------

def test_refresh_rejects_an_unknown_subject(client, client_credential) -> None:
    token = sign_token("00000000-0000-0000-0000-000000000000")
    r = client.post("/api/v1/auth/refresh",
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


# -----------------------------------------------------------------------------

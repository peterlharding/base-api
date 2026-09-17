"""The /api/v1/users routes require a bearer token.

These use `protected_client`, which leaves the real dependency in force.
The default `client` fixture overrides it, so no other test file can show
whether a route is actually protected - that is what this file is for.
"""

import re

from datetime import timedelta

import jwt
import pytest
from sqlalchemy import insert, update

from app.auth.handler import sign_token
from app.db.session import SessionLocal
from app.models import ApplicationUser


GUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

def _crud_routes():
    """Every /api/v1 route except the auth endpoints, from the live schema.

    Derived rather than listed, so a resource added later is covered without
    anyone remembering to extend this file.
    """
    from app.main import app

    out = []
    for path, ops in sorted(app.openapi()["paths"].items()):
        if not path.startswith("/api/v1") or path.startswith("/api/v1/auth"):
            continue
        probe = re.sub(r"\{[^}]+\}", "1", path)
        for method in ops:
            out.append((method, probe, {} if method in ("post", "put", "patch") else None))
    return out


ROUTES = _crud_routes()


# -----------------------------------------------------------------------------

@pytest.fixture()
def token_user():
    """An active user to sign tokens for, created without going through the API."""
    with SessionLocal() as s:
        s.execute(insert(ApplicationUser).values(
            username="token-owner", guid=GUID, is_active=True))
        s.commit()
    return GUID


def _call(c, method, path, body, headers=None):
    fn = getattr(c, method)
    return fn(path, json=body, headers=headers or {}) if body is not None \
        else fn(path, headers=headers or {})


# -----------------------------------------------------------------------------

@pytest.mark.parametrize("method,path,body", ROUTES)
def test_route_rejects_a_missing_token(protected_client, method, path, body) -> None:
    r = _call(protected_client, method, path, body)
    assert r.status_code in (401, 403), f"{method.upper()} {path} is unprotected"


# -----------------------------------------------------------------------------

@pytest.mark.parametrize("method,path,body", ROUTES)
def test_route_accepts_a_valid_token(protected_client, token_user, method, path, body) -> None:
    headers = {"Authorization": f"Bearer {sign_token(token_user)}"}
    r = _call(protected_client, method, path, body, headers)
    assert r.status_code != 401, f"{method.upper()} {path} rejected a valid token"


# -----------------------------------------------------------------------------

def test_expired_token_is_rejected(protected_client, token_user) -> None:
    token = sign_token(token_user, ttl=timedelta(minutes=-1))
    r = protected_client.get("/api/v1/users",
                             headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token expired"


# -----------------------------------------------------------------------------

def test_forged_token_is_rejected(protected_client, token_user) -> None:
    forged = jwt.encode({"sub": token_user, "exp": 9999999999},
                        "a-different-secret-long-enough-to-sign", algorithm="HS256")
    r = protected_client.get("/api/v1/users",
                             headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid token signature"


# -----------------------------------------------------------------------------

def test_token_for_an_unknown_user_is_rejected(protected_client) -> None:
    token = sign_token("00000000-0000-0000-0000-000000000000")
    r = protected_client.get("/api/v1/users",
                             headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Not a valid user"


# -----------------------------------------------------------------------------

def test_token_for_a_deactivated_user_is_rejected(protected_client, token_user) -> None:
    """Deactivating a user must invalidate tokens already issued to them."""
    token = sign_token(token_user)
    assert protected_client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {token}"}).status_code == 200

    with SessionLocal() as s:
        s.execute(update(ApplicationUser)
                  .where(ApplicationUser.guid == token_user)
                  .values(is_active=False))
        s.commit()

    r = protected_client.get("/api/v1/users",
                             headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "User is not active"


# -----------------------------------------------------------------------------

def test_malformed_authorization_header_is_rejected(protected_client) -> None:
    for header in ("", "Bearer", "Basic abc", "Bearer not.a.token"):
        r = protected_client.get("/api/v1/users",
                                 headers={"Authorization": header} if header else {})
        assert r.status_code in (401, 403), f"accepted {header!r}"


# -----------------------------------------------------------------------------

def test_authenticate_works_without_a_bearer_token(protected_client) -> None:
    """The one route that must stay open, or no client can ever obtain a token.

    Asserted with real credentials and no Authorization: Bearer header, so a
    401 here would mean the endpoint had been put behind the very token it
    exists to issue.  Checking only "not 403" would not have caught that.
    """
    import base64

    from sqlalchemy import insert, update

    from app.auth.password import hash_password
    from app.db.session import SessionLocal
    from app.models import ApiCredential, ApplicationUser

    with SessionLocal() as s:
        s.execute(insert(ApiCredential).values(
            email="probe@example.com", hashed_password=hash_password("client-pw")))
        s.execute(insert(ApplicationUser).values(
            username="probe-user", guid="12121212-3434-5656-7878-909090909090",
            is_active=True, hashed_password=hash_password("user-pw")))
        s.commit()

    basic = base64.b64encode(b"probe@example.com:client-pw").decode()

    r = protected_client.post(
        "/api/v1/auth/authenticate",
        json={"username": "probe-user", "password": "user-pw"},
        headers={"Authorization": f"Basic {basic}"},
    )

    assert r.status_code == 200, "authenticate must not require a bearer token"
    assert r.json()["token"]


# -----------------------------------------------------------------------------

def test_every_crud_route_is_protected(protected_client) -> None:
    """No /api/v1 route outside auth may be reachable without a token.

    Derived from the live schema, so adding an unprotected resource fails
    here rather than shipping quietly.
    """
    unprotected = [
        f"{method.upper()} {path}"
        for method, path, body in ROUTES
        if _call(protected_client, method, path, body).status_code not in (401, 403)
    ]
    assert not unprotected, f"reachable without a token: {unprotected}"


# -----------------------------------------------------------------------------

def test_route_count_is_what_we_think(protected_client) -> None:
    """Guards against _crud_routes() silently matching nothing."""
    assert len(ROUTES) >= 60, f"only {len(ROUTES)} routes discovered"

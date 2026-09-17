"""Credentials must not reach stdout, stderr or the logger.

This has regressed three times while the auth code was being adapted: a
print of the HTTPBasicCredentials object includes the plaintext password,
and a log of the token or the signing secret hands over the credential
itself.  Whatever collects process output then holds them.

Asserted rather than reviewed, because a print added while debugging is
exactly the kind of thing that survives to production.
"""

import base64
import logging

from sqlalchemy import insert, select

from app.auth.password import hash_password
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import ApiCredential, ApplicationUser


CLIENT, SECRET = "quiet@example.com", "client-secret-value"
USER, USER_PW = "quiet-user", "user-secret-value"


def _sign_in(client):
    with SessionLocal() as s:
        if not s.scalar(select(ApiCredential).where(ApiCredential.email == CLIENT)):
            s.execute(insert(ApiCredential).values(
                email=CLIENT, hashed_password=hash_password(SECRET)))
        if not s.scalar(select(ApplicationUser).where(ApplicationUser.username == USER)):
            s.execute(insert(ApplicationUser).values(
                username=USER, guid="99999999-1111-2222-3333-444444444444",
                is_active=True, hashed_password=hash_password(USER_PW)))
        s.commit()

    raw = base64.b64encode(f"{CLIENT}:{SECRET}".encode()).decode()
    return client.post("/api/v1/auth/authenticate",
                       json={"username": USER, "password": USER_PW},
                       headers={"Authorization": f"Basic {raw}"})


# -----------------------------------------------------------------------------

def test_a_successful_sign_in_emits_no_secrets(client, capfd, caplog) -> None:
    with caplog.at_level(logging.DEBUG):
        r = _sign_in(client)
    assert r.status_code == 200

    emitted = capfd.readouterr()
    haystack = emitted.out + emitted.err + caplog.text

    for secret, label in (
        (SECRET,  "the client secret"),
        (USER_PW, "the user password"),
        (get_settings().jwt_secret, "the signing secret"),
        (r.json()["token"], "the issued token"),
    ):
        assert secret not in haystack, f"{label} was written to output"


# -----------------------------------------------------------------------------

def test_a_failed_sign_in_emits_no_secrets(client, capfd, caplog) -> None:
    _sign_in(client)
    raw = base64.b64encode(f"{CLIENT}:{SECRET}".encode()).decode()

    with caplog.at_level(logging.DEBUG):
        r = client.post("/api/v1/auth/authenticate",
                        json={"username": USER, "password": "wrong-password-value"},
                        headers={"Authorization": f"Basic {raw}"})
    assert r.status_code == 401

    emitted = capfd.readouterr()
    haystack = emitted.out + emitted.err + caplog.text

    assert "wrong-password-value" not in haystack
    assert SECRET not in haystack


# -----------------------------------------------------------------------------

def test_a_rejected_token_is_not_logged(client, capfd, caplog) -> None:
    from app.auth.handler import sign_token

    token = sign_token("00000000-0000-0000-0000-000000000000")

    with caplog.at_level(logging.DEBUG):
        client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})

    emitted = capfd.readouterr()
    assert token not in emitted.out + emitted.err + caplog.text

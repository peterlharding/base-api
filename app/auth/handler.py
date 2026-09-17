#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""JWT signing and decoding.

The only place that knows the token shape, so the authenticate and refresh
endpoints cannot drift apart from the bearer dependency that reads what they
issue.
"""
# -----------------------------------------------------------------------------

import uuid

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt


# -----------------------------------------------------------------------------

from app.core.config import JWT_SECRET_PLACEHOLDER, get_settings


# -----------------------------------------------------------------------------

TOKEN_TTL = timedelta(minutes=60)

# RFC 7518 section 3.2: an HMAC key for HS256 must be at least as long as the
# hash output.  PyJWT warns below this; here it is an error, because a weak
# signing key is not something to discover in a log.
_MIN_SECRET_BYTES = 32


# -----------------------------------------------------------------------------

def _secret() -> str:
    """The signing secret, or a clear failure saying how to set it."""
    secret = get_settings().jwt_secret

    if not secret or secret == JWT_SECRET_PLACEHOLDER:
        raise RuntimeError(
            "JWT_SECRET is not set. Add it to the repo-root .env "
            "(see setup/env.template); there is deliberately no default."
        )

    if len(secret.encode()) < _MIN_SECRET_BYTES:
        raise RuntimeError(
            f"JWT_SECRET is {len(secret.encode())} bytes; "
            f"HS256 needs at least {_MIN_SECRET_BYTES}."
        )

    return secret


# -----------------------------------------------------------------------------

def sign_token(user_guid: str, ttl: timedelta = TOKEN_TTL) -> str:
    """Return a signed JWT for a user.

    ``jti`` is a fresh uuid on every call so a single token can be revoked
    without invalidating every other token held by the same user - that is
    what token_blacklist stores.
    """
    now = datetime.now(timezone.utc)

    return jwt.encode(
        {
            "sub": str(user_guid),
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + ttl,
        },
        _secret(),
        algorithm=get_settings().jwt_algorithm,
    )


# -----------------------------------------------------------------------------

def decode_token(token: str, *, verify_exp: bool = True) -> dict[str, Any]:
    """Decode and verify a token, raising on anything wrong with it.

    Deliberately not swallowing exceptions: an expired token, a forged
    signature and a malformed string each need a different response, and
    returning {} for all three made them indistinguishable.  Callers catch
    the specific jwt exceptions they care about.

    ``verify_exp=False`` is for the refresh endpoint, which accepts a
    recently expired token but still requires a valid signature.
    """
    return jwt.decode(
        token,
        _secret(),
        algorithms=[get_settings().jwt_algorithm],
        options={"verify_exp": verify_exp},
    )


# -----------------------------------------------------------------------------

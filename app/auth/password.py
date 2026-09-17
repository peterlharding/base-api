#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""bcrypt password hashing.

One place that knows how a password is stored, so the models and the seed
data cannot disagree about it.

bcrypt salts each hash itself, so the salt travels inside the digest and
there is no separate column.  It also truncates at 72 bytes, which is why
``hash_password`` rejects anything longer rather than silently ignoring the
tail - two distinct passwords sharing a 72-byte prefix would otherwise both
verify.

Run this module to generate a hash for the seed data:

    python -m app.auth.password 'sample-password'
"""
# -----------------------------------------------------------------------------

import bcrypt


# -----------------------------------------------------------------------------

_MAX_BYTES = 72


# -----------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Return a bcrypt digest, salt included, as ASCII text."""
    raw = password.encode("utf-8")
    if len(raw) > _MAX_BYTES:
        raise ValueError(
            f"password is {len(raw)} bytes; bcrypt truncates at {_MAX_BYTES}"
        )
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("ascii")


# -----------------------------------------------------------------------------

def verify_password(password: str, hashed: str | None) -> bool:
    """Check a password against a stored digest.

    False rather than an exception for every failure, including a NULL or
    malformed digest, so a caller cannot tell a missing password apart from a
    wrong one.

    Nothing here prints or logs either argument.  A plaintext password on
    stdout ends up in whatever collects it, and the digest is the one thing
    an attacker needs to mount an offline attack.
    """

    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        sys.exit("usage: python -m app.auth.password <password>")
    print(hash_password(sys.argv[1]))


# -----------------------------------------------------------------------------

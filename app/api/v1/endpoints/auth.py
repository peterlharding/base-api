#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Authentication endpoints, served under /api/v1/auth.

Two layers have to pass before a token is issued:

    HTTP Basic   -> api_credentials    which client is calling
    JSON body    -> application_user   which user is signing in

The Basic layer is deliberate: it keeps the token endpoint from being open
to anyone who can reach the host, so a stolen user password alone is not
enough to mint a token.
"""
# -----------------------------------------------------------------------------

import jwt

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.logger        import logger
from app.utils         import record_login_session
from app.models        import (
    ApiCredential,
    ApplicationUser,
    LoginSession,
    TokenBlacklist,
)
from app.db.session    import get_db
from app.auth.handler  import TOKEN_TTL, decode_token, sign_token
from app.auth.bearer   import jwt_bearer


# -----------------------------------------------------------------------------

router   = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBasic()

# How long past expiry a token may still be exchanged for a fresh one.
REFRESH_GRACE = timedelta(hours=24)


# -----------------------------------------------------------------------------
# Same 401 for "no such client", "wrong client secret", "no such user" and
# "wrong password".  Distinguishing them would let a caller enumerate valid
# usernames.

def _unauthorised(scheme: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication",
        headers={"WWW-Authenticate": scheme},
    )


# =============================================================================

class Credentials(BaseModel):
    """The user signing in, in the request body."""

    model_config = {"extra": "forbid"}

    username: str
    password: str


# -----------------------------------------------------------------------------

class AuthenticatedUser(BaseModel):
    """The user, as returned alongside a token.

    Mirrors the columns that exist on application_user.  hashed_password is
    absent on purpose, as it is everywhere else.
    """

    id: int
    guid: UUID | None = None
    username: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    last_login_date: datetime | None = None


# -----------------------------------------------------------------------------

class AuthPayload(BaseModel):
    token: str
    refresh_interval: int
    user: AuthenticatedUser


# -----------------------------------------------------------------------------

def _issue(user: ApplicationUser) -> dict:
    return {
        "token": sign_token(user.guid),
        "refresh_interval": int(TOKEN_TTL.total_seconds()),
        "user": user,
    }


# -----------------------------------------------------------------------------

def _bearer_token(request: Request) -> str:
    """The raw token from the Authorization header.

    The dependency has already verified it by the time a route body runs, but
    it hands back the user rather than the credential, and revoking a token
    needs the token.
    """
    header = request.headers.get("Authorization", "")

    if not header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return header.removeprefix("Bearer ").strip()


# -----------------------------------------------------------------------------

def _touch_session(db: Session, old_token: str, user) -> None:
    """Advance last_seen on the session the refreshed token came from.

    Best effort: a refresh whose original sign-in was never recorded, or was
    recorded before this existed, simply has nothing to update.
    """
    import hashlib

    from app.models import LoginSession

    try:
        digest = hashlib.sha256(old_token.encode()).digest()
        session = db.scalar(
            select(LoginSession).where(LoginSession.session_token_hash == digest)
        )
        if session is not None:
            session.last_seen = datetime.now(timezone.utc)
            db.commit()

    except Exception as ex:                      # noqa: BLE001
        db.rollback()
        logger.warning("could not touch login session for user id %s: %s", user.id, ex)


# =============================================================================

@router.post(
    "/authenticate",
    response_model=AuthPayload
)
def authenticate(
    body: Credentials,
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """Exchange client Basic Auth plus user credentials for a token."""

    client = db.scalar(
        select(ApiCredential).where(ApiCredential.email == credentials.username)
    )

    if client is None or not client.is_correct_password(credentials.password):
        logger.info("authenticate: basic auth rejected")
        raise _unauthorised("Basic")

    user = db.scalar(
        select(ApplicationUser).where(ApplicationUser.username == body.username)
    )

    if user is None or not user.is_correct_password(body.password):
        logger.info("authenticate: user credentials rejected")
        raise _unauthorised("Basic")

    if not user.is_active:
        logger.info("authenticate: inactive user rejected")
        raise _unauthorised("Basic")

    user.last_login_date = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    issued = _issue(user)

    record_login_session(db, user, issued["token"], request)

    logger.info("authenticate: issued a token for user id %s", user.id)

    return issued


# -----------------------------------------------------------------------------

@router.post(
    "/refresh",
    response_model=AuthPayload
)
def refresh(request: Request, db: Session = Depends(get_db)) -> dict:
    """Exchange a valid, or recently expired, token for a fresh one.

    The signature must still verify - only the expiry is waived, and only
    within REFRESH_GRACE.  An expired token is therefore usable to obtain a
    new one for a day, but a forged one never is.
    """
    header = request.headers.get("Authorization", "")

    if not header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = header.removeprefix("Bearer ").strip()

    try:
        payload = decode_token(token, verify_exp=False)
    except jwt.PyJWTError:
        raise _unauthorised("Bearer") from None

    # A revoked token must not be exchangeable for a fresh one, or logging
    # out would achieve nothing: refresh does not go through jwt_bearer, so
    # the blacklist has to be consulted here too.
    jti = payload.get("jti")
    if jti and TokenBlacklist.check_blacklist(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expiry = payload.get("exp")
    if expiry is None:
        raise _unauthorised("Bearer")

    expired_at = datetime.fromtimestamp(expiry, tz=timezone.utc)
    if datetime.now(timezone.utc) - expired_at > REFRESH_GRACE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token too old to refresh",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalar(
        select(ApplicationUser).where(ApplicationUser.guid == payload.get("sub"))
    )

    if user is None or not user.is_active:
        raise _unauthorised("Bearer")

    issued = _issue(user)

    _touch_session(db, token, user)

    logger.info("refresh: reissued a token for user id %s", user.id)

    return issued


# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    actor: ApplicationUser = Depends(jwt_bearer),
    db: Session = Depends(get_db),
) -> None:
    """Revoke the token this request was made with.

    The token's jti goes into token_blacklist, which the bearer dependency
    checks on every request, so the token stops working immediately rather
    than merely being forgotten by the client.  Only this token is revoked -
    signing out on one device does not sign the user out everywhere.

    The matching login_session is stamped revoked_at, so the session list
    shows what happened rather than a row that simply stops being refreshed.

    Idempotent from the caller's point of view: a second attempt with the
    same token is rejected by the dependency with 401, because by then the
    token really is revoked.
    """
    import hashlib

    token   = _bearer_token(request)
    payload = decode_token(token)
    jti     = payload.get("jti")

    if jti is None:
        # Tokens have carried a jti since they were first issued; one without
        # is not something to guess about.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token carries no id and cannot be revoked",
        )

    db.add(TokenBlacklist(
        jti=jti,
        user_id=actor.id,
        reason="logout",
        expiry=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
    ))

    session = db.scalar(
        select(LoginSession).where(
            LoginSession.session_token_hash == hashlib.sha256(token.encode()).digest()
        )
    )
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)

    # Opportunistic: the table only grows here, so this is the one place that
    # can keep it in check without a scheduler.  The row just added has a
    # future expiry and is not touched.  scripts/prune_blacklist.py does the
    # same thing for a deployment where nobody logs out for a long stretch.
    pruned = TokenBlacklist.prune_expired(db)

    db.commit()

    if pruned:
        logger.info("logout: pruned %s expired blacklist row(s)", pruned)

    logger.info("logout: revoked a token for user id %s", actor.id)


# -----------------------------------------------------------------------------

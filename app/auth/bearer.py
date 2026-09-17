#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Bearer token dependency.

Protect a route by depending on it:

    @router.get("/thing", dependencies=[Depends(jwt_bearer)])

or take the authenticated user:

    def handler(user: ApplicationUser = Depends(jwt_bearer)):
"""
# -----------------------------------------------------------------------------

import jwt

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.auth.handler import decode_token
from app.db.session   import get_db
from app.logger       import logger
from app.models       import ApplicationUser, TokenBlacklist


# -----------------------------------------------------------------------------
# Every failure is the same 401 with the same header.  The detail says which
# check failed because that is useful to a legitimate caller, but nothing here
# logs the token, the payload or the secret: they would end up in whatever
# collects stdout.

def _unauthorised(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


# -----------------------------------------------------------------------------

class JWTBearer(HTTPBearer):
    """Resolve a bearer token to the ApplicationUser that owns it."""

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    # -------------------------------------------------------------------------

    async def __call__(                                    # type: ignore[override]
        self,
        request: Request,
        db: Session = Depends(get_db),
    ) -> ApplicationUser:
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(request)

        if credentials is None:
            raise _unauthorised("Not authenticated")

        if credentials.scheme != "Bearer":
            raise _unauthorised("Invalid authentication scheme")

        return self.resolve(credentials.credentials, db)

    # -------------------------------------------------------------------------

    def resolve(self, token: str, db: Session) -> ApplicationUser:
        """Verify a token and return its user, or raise 401.

        Returns the user rather than a bool so a caller cannot forget to act
        on the answer - the previous version returned True/False and the
        check on the result was commented out, which meant an invalid token
        still got through.
        """
        try:
            payload = decode_token(token)

        except jwt.ExpiredSignatureError:
            raise _unauthorised("Token expired") from None
        except jwt.InvalidSignatureError:
            raise _unauthorised("Invalid token signature") from None
        except jwt.PyJWTError:
            raise _unauthorised("Invalid token") from None

        jti = payload.get("jti")
        if jti and TokenBlacklist.check_blacklist(db, jti):
            logger.info("rejected a blacklisted token")
            raise _unauthorised("Token has been revoked")

        subject = payload.get("sub")
        if not subject:
            raise _unauthorised("Token carries no subject")

        user = db.scalar(select(ApplicationUser).where(ApplicationUser.guid == subject))

        if user is None:
            raise _unauthorised("Not a valid user")

        if not user.is_active:
            raise _unauthorised("User is not active")

        return user


# -----------------------------------------------------------------------------
# One instance, so routes share it rather than constructing their own.

jwt_bearer = JWTBearer()


# -----------------------------------------------------------------------------

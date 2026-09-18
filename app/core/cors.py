#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Cross-origin access, configured from CORS_ORIGINS in the repo-root .env.

Off unless the setting names at least one origin.  The API was built for a
server-to-server caller, which needs no CORS at all, so switching it on is a
deliberate act rather than something a deployment inherits: a browser cannot
read a response the API never agreed to share, and the default should be the
one that shares nothing.
"""
# -----------------------------------------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# -----------------------------------------------------------------------------

from app.core.config import Settings
from app.logger      import logger


# -----------------------------------------------------------------------------
# The methods the API actually serves.  Listed rather than "*" so the browser
# is told the real surface, and so a method added to a router without a
# thought about CORS shows up as a failing test rather than as a preflight
# rejection someone has to debug from the network tab.
#
# tests/test_cors.py checks this against the live OpenAPI schema.

METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

# Authorization carries both the bearer token and the Basic credential on
# /auth/authenticate; without it every request from a browser is anonymous.
HEADERS = ["Authorization", "Content-Type"]


# -----------------------------------------------------------------------------

def origins(settings: Settings) -> list[str]:
    """The configured origins, or an empty list.

    Parsed from a comma-separated string rather than typed as list[str],
    because pydantic-settings runs a complex annotation through json.loads
    first: CORS_ORIGINS=http://localhost:5173 is not JSON and the application
    would fail to start with a parse error rather than a useful one.
    """
    return [part.strip() for part in settings.cors_origins.split(",") if part.strip()]


# -----------------------------------------------------------------------------

def configure_cors(app: FastAPI, settings: Settings) -> list[str]:
    """Install the middleware if any origin is configured.  Returns them.

    Credentials are deliberately not allowed.  Authentication here is a
    bearer token in a header, which a browser sends without them; turning
    them on would attach cookies to cross-origin requests and buy nothing
    this API uses.

    A wildcard is refused outright in production.  Every other origin check
    is a list someone maintains, and "*" is the one value that silently
    stops being one - the same reasoning that has handler.py refuse the
    placeholder JWT secret by name.
    """
    configured = origins(settings)

    if not configured:
        logger.info("cors: no origins configured, middleware not installed")
        return []

    if "*" in configured:
        if settings.release == "prod":
            raise RuntimeError(
                "CORS_ORIGINS is '*' on a prod release. Name the origins that "
                "may call this API; a wildcard lets any site on the internet "
                "read authenticated responses from a browser that holds a token."
            )

        logger.warning(
            "cors: allowing any origin (CORS_ORIGINS='*') on the %s release",
            settings.release,
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured,
        allow_credentials=False,
        allow_methods=METHODS,
        allow_headers=HEADERS,
    )

    logger.info("cors: allowing %s", ", ".join(configured))

    return configured


# -----------------------------------------------------------------------------

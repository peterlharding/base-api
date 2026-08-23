#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Version 1 API router: everything under /api/v1 lives in this tree."""
# -----------------------------------------------------------------------------

from fastapi import APIRouter

from app.api.v1.endpoints import users


# -----------------------------------------------------------------------------

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(users.router)


# -----------------------------------------------------------------------------

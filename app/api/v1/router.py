#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Version 1 API router: everything under /api/v1 lives in this tree."""
# -----------------------------------------------------------------------------

from fastapi import APIRouter

from app.api.v1.endpoints import (
    access,
    accounts,
    attachments,
    contacts,
    documents,
    events,
    leads,
    notes,
    opportunities,
    quotes,
    tasks,
    users,
)


# -----------------------------------------------------------------------------

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(users.router)
api_router.include_router(accounts.router)
api_router.include_router(contacts.router)
api_router.include_router(documents.router)
api_router.include_router(events.router)
api_router.include_router(notes.router)
api_router.include_router(tasks.router)
api_router.include_router(opportunities.router)
api_router.include_router(leads.router)
api_router.include_router(quotes.router)
api_router.include_router(access.router)
api_router.include_router(attachments.router)


# -----------------------------------------------------------------------------

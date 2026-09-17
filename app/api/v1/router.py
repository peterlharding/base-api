#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Version 1 API router: everything under /api/v1 lives in this tree."""
# -----------------------------------------------------------------------------

from fastapi import APIRouter


# -----------------------------------------------------------------------------

from app.api.v1.endpoints import (
    access,
    accounts,
    attachments,
    audit_log,
    auth,
    contacts,
    documents,
    events,
    instance_metadata,
    leads,
    login_sessions,
    notes,
    opportunities,
    quotes,
    tasks,
    user_roles,
    users,
)


# -----------------------------------------------------------------------------

api_v1_router = APIRouter(prefix="/api/v1")

# auth first: it is the entry point, and it is the only router here that is
# not plain CRUD over a table.
api_v1_router.include_router(auth.router)

api_v1_router.include_router(access.router)
api_v1_router.include_router(accounts.router)
api_v1_router.include_router(attachments.router)
api_v1_router.include_router(contacts.router)
api_v1_router.include_router(documents.router)
api_v1_router.include_router(audit_log.router)
api_v1_router.include_router(events.router)
api_v1_router.include_router(instance_metadata.router)
api_v1_router.include_router(login_sessions.router)
api_v1_router.include_router(leads.router)
api_v1_router.include_router(notes.router)
api_v1_router.include_router(opportunities.router)
api_v1_router.include_router(quotes.router)
api_v1_router.include_router(tasks.router)
api_v1_router.include_router(user_roles.router)
api_v1_router.include_router(users.router)


# -----------------------------------------------------------------------------

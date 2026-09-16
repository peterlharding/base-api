#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""
SQLAlchemy models for the application database.

Importing this package registers every model on Base.metadata, which is what
alembic autogenerate (db/alembic/env.py) and the test suite's per-test
TRUNCATE rely on.  A model that is not imported here is invisible to both:
autogenerate will propose dropping its table, and the suite will not clean it
between tests.
"""
# -----------------------------------------------------------------------------
# API tables (migrations 0001-0002)

from .api_credentials    import ApiCredential
from .application_user   import ApplicationUser
from .audit_log          import AuditLog
from .instance_metadata  import instance_metadata
from .login_session      import LoginSession
from .token_blacklist    import TokenBlacklist


# -----------------------------------------------------------------------------
# CRM tables (migration 0003)

from .access             import Access
from .account            import Account
from .attachment         import Attachment
from .contact            import Contact
from .document           import Document
from .event              import Event
from .lead               import Lead
from .note               import Note
from .opportunity        import Opportunity
from .quote              import Quote
from .task               import Task
from .user_role          import UserRole


# -----------------------------------------------------------------------------

__all__ = [
    # API
    "ApiCredential",
    "ApplicationUser",
    "AuditLog",
    "LoginSession",
    "TokenBlacklist",
    "instance_metadata",
    # CRM
    "Access",
    "Account",
    "Attachment",
    "Contact",
    "Document",
    "Event",
    "Lead",
    "Note",
    "Opportunity",
    "Quote",
    "Task",
    "UserRole",
]


# -----------------------------------------------------------------------------

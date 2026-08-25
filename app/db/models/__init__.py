"""SQLAlchemy models for the base_api database.

Importing this package registers every model on Base.metadata, which is
what alembic autogenerate (db/alembic/env.py) and the test suite rely on.
"""

from app.db.models.api_credentials import ApiCredential
from app.db.models.application_user import ApplicationUser
from app.db.models.instance_metadata import instance_metadata
from app.db.models.login_session import LoginSession
from app.db.models.token_blacklist import TokenBlacklist

__all__ = [
    "ApiCredential",
    "ApplicationUser",
    "LoginSession",
    "TokenBlacklist",
    "instance_metadata",
]

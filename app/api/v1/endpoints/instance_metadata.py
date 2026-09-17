#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Read-only endpoint for instance_metadata, at /api/v1/instance-metadata.

A singleton, so it returns one object rather than a list and there is no
path parameter.  The table enforces that with a unique index on (true).

Two of the four values are read at runtime rather than from the row:

    release, db_version, notes   the row - what this database was built as
    app_version                  pyproject.toml - what is actually running
    alembic_revision             alembic_version - what the schema is at

A version stamped into a row goes stale the moment the application is
upgraded without a migration, which is most upgrades.  Reporting the running
values means the answer is about the process serving the request.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1       import schemas
from app.auth.bearer  import jwt_bearer
from app.core.version import app_version
from app.models       import instance_metadata
from app.db.session   import get_db


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/instance-metadata", tags=["instance-metadata"])


# -----------------------------------------------------------------------------

@router.get("", response_model=schemas.InstanceMetadata,
            dependencies=[Depends(jwt_bearer)])
def get_instance_metadata(db: Session = Depends(get_db)) -> dict:
    """Describe the backend serving this request."""
    row = db.execute(select(instance_metadata)).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "instance_metadata holds no row; "
                "migration 0006 stamps it on a migrated database"
            ),
        )

    revision = db.scalar(text("SELECT version_num FROM alembic_version"))

    return {
        "release":          row["release"],
        "app_version":      app_version(),
        "db_version":       row["db_version"],
        "alembic_revision": revision,
        "notes":            row["notes"],
        "updated_at":       row["updated_at"],
    }


# -----------------------------------------------------------------------------

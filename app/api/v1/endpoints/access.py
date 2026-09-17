#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for access, served under /api/v1/access.

The path parameter is the surrogate key ``id``.

Served under /api/v1/access - the noun is uncountable, so the collection and
the singular share a path.

This table carries no audit columns: no created_at / updated_at / *_by_id,
and so no set_updated_at trigger.  ``last_referenced_date`` is an ordinary
writable field, not a server-maintained stamp.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import Access
from app.db.session  import get_db
from app.auth.bearer import jwt_bearer



# -----------------------------------------------------------------------------

router = APIRouter(prefix="/access", tags=["access"])

_LABEL = "access"


# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[schemas.Access],
    dependencies=[Depends(jwt_bearer)]
)
def list_access_rows(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Access]:
    """Page through access in id order."""
    stmt = select(Access).order_by(Access.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post(
    "",
    response_model=schemas.Access,
    dependencies=[Depends(jwt_bearer)],
    status_code=status.HTTP_201_CREATED,
)
def create_access(payload: schemas.AccessCreate, db: Session = Depends(get_db)) -> Access:
    row = Access(**payload.model_dump(exclude_unset=True))
    db.add(row)
    commit(db, Access, _LABEL)
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.get(
    "/{access_pk}",
    response_model=schemas.Access,
    dependencies=[Depends(jwt_bearer)]
)
def get_access(access_pk: int, db: Session = Depends(get_db)) -> Access:
    """Fetch a single access by surrogate key."""
    return get_or_404(db, Access, access_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put(
    "/{access_pk}",
    response_model=schemas.Access,
    dependencies=[Depends(jwt_bearer)]
)
def update_access(
    access_pk: int,
    payload: schemas.AccessUpdate,
    db: Session = Depends(get_db),
) -> Access:
    """Patch a access: only the fields present in the payload are changed."""
    row = get_or_404(db, Access, access_pk, _LABEL)
    apply_update(row, payload.model_dump(exclude_unset=True))
    commit(db, Access, _LABEL)
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.delete(
    "/{access_pk}",
    dependencies=[Depends(jwt_bearer)],
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_access(access_pk: int, db: Session = Depends(get_db)) -> None:
    row = get_or_404(db, Access, access_pk, _LABEL)
    db.delete(row)
    commit(db, Access, _LABEL)


# -----------------------------------------------------------------------------

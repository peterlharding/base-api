#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for attachment, served under /api/v1/attachments.

The path parameter is the surrogate key ``id``.

``parent_id`` points at the owning record but carries no discriminator and
no foreign key, so nothing here validates it.  The table stores metadata
only - ``body_length`` is recorded but no file content is held.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import Attachment
from app.db.session  import get_db
from app.auth.bearer import jwt_bearer


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/attachments", tags=["attachments"])

_LABEL = "attachment"


# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[schemas.Attachment],
    dependencies=[Depends(jwt_bearer)]
)
def list_attachments(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Attachment]:
    """Page through attachment in id order."""
    stmt = select(Attachment).order_by(Attachment.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post(
    "",
    response_model=schemas.Attachment,
    dependencies=[Depends(jwt_bearer)],
    status_code=status.HTTP_201_CREATED
)
def create_attachment(payload: schemas.AttachmentCreate, db: Session = Depends(get_db)) -> Attachment:
    row = Attachment(**payload.model_dump(exclude_unset=True))
    db.add(row)
    commit(db, Attachment, _LABEL)
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.get(
    "/{attachment_pk}",
    response_model=schemas.Attachment,
    dependencies=[Depends(jwt_bearer)]
)
def get_attachment(attachment_pk: int, db: Session = Depends(get_db)) -> Attachment:
    """Fetch a single attachment by surrogate key."""
    return get_or_404(db, Attachment, attachment_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put(
    "/{attachment_pk}",
    response_model=schemas.Attachment,
    dependencies=[Depends(jwt_bearer)]
)
def update_attachment(
    attachment_pk: int,
    payload: schemas.AttachmentUpdate,
    db: Session = Depends(get_db),
) -> Attachment:
    """Patch a attachment: only the fields present in the payload are changed."""
    row = get_or_404(db, Attachment, attachment_pk, _LABEL)
    apply_update(row, payload.model_dump(exclude_unset=True))
    commit(db, Attachment, _LABEL)
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.delete(
    "/{attachment_pk}",
    dependencies=[Depends(jwt_bearer)],
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_attachment(attachment_pk: int, db: Session = Depends(get_db)) -> None:
    row = get_or_404(db, Attachment, attachment_pk, _LABEL)
    db.delete(row)
    commit(db, Attachment, _LABEL)


# -----------------------------------------------------------------------------

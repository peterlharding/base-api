#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for document, served under /api/v1/documents.

The path parameter is the surrogate key ``id``.  The ``guid`` column is an
ordinary field on the model.

``author_id`` and ``folder_ref`` are unconstrained: the CRM tables declare
no foreign keys, so nothing here validates that they point at an existing
row.  The table stores metadata and a ``url`` only - no file content.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import Document
from app.db.session  import get_db


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/documents", tags=["documents"])

_LABEL = "document"


# -----------------------------------------------------------------------------

@router.get("", response_model=list[schemas.Document])
def list_documents(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Document]:
    """Page through document in id order."""
    stmt = select(Document).order_by(Document.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post("", response_model=schemas.Document, status_code=status.HTTP_201_CREATED)
def create_document(payload: schemas.DocumentCreate, db: Session = Depends(get_db)) -> Document:
    document = Document(**payload.model_dump(exclude_unset=True))
    db.add(document)
    commit(db, Document, _LABEL)
    db.refresh(document)
    return document


# -----------------------------------------------------------------------------

@router.get("/{document_pk}", response_model=schemas.Document)
def get_document(document_pk: int, db: Session = Depends(get_db)) -> Document:
    """Fetch a single document by surrogate key."""
    return get_or_404(db, Document, document_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put("/{document_pk}", response_model=schemas.Document)
def update_document(
    document_pk: int,
    payload: schemas.DocumentUpdate,
    db: Session = Depends(get_db),
) -> Document:
    """Patch a document: only the fields present in the payload are changed."""
    document = get_or_404(db, Document, document_pk, _LABEL)
    apply_update(document, payload.model_dump(exclude_unset=True))
    commit(db, Document, _LABEL)
    db.refresh(document)
    return document


# -----------------------------------------------------------------------------

@router.delete("/{document_pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_pk: int, db: Session = Depends(get_db)) -> None:
    document = get_or_404(db, Document, document_pk, _LABEL)
    db.delete(document)
    commit(db, Document, _LABEL)


# -----------------------------------------------------------------------------

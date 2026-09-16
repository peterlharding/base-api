#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for contact, served under /api/v1/contacts.

The path parameter is the surrogate key ``id``.  The ``guid`` column (an
18-character Salesforce-style id) is an ordinary field on the model.

``account_id``, ``owner_id`` and ``reports_to_id`` are plain bigints: the CRM
tables declare no foreign keys, so nothing here validates that they point at
an existing row.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import Contact
from app.db.session  import get_db


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/contacts", tags=["contacts"])

_LABEL = "contact"


# -----------------------------------------------------------------------------

@router.get("", response_model=list[schemas.Contact])
def list_contacts(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Contact]:
    """Page through contact in id order."""
    stmt = select(Contact).order_by(Contact.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post("", response_model=schemas.Contact, status_code=status.HTTP_201_CREATED)
def create_contact(payload: schemas.ContactCreate, db: Session = Depends(get_db)) -> Contact:
    contact = Contact(**payload.model_dump(exclude_unset=True))
    db.add(contact)
    commit(db, Contact, _LABEL)
    db.refresh(contact)
    return contact


# -----------------------------------------------------------------------------

@router.get("/{contact_pk}", response_model=schemas.Contact)
def get_contact(contact_pk: int, db: Session = Depends(get_db)) -> Contact:
    """Fetch a single contact by surrogate key."""
    return get_or_404(db, Contact, contact_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put("/{contact_pk}", response_model=schemas.Contact)
def update_contact(
    contact_pk: int,
    payload: schemas.ContactUpdate,
    db: Session = Depends(get_db),
) -> Contact:
    """Patch a contact: only the fields present in the payload are changed."""
    contact = get_or_404(db, Contact, contact_pk, _LABEL)
    apply_update(contact, payload.model_dump(exclude_unset=True))
    commit(db, Contact, _LABEL)
    db.refresh(contact)
    return contact


# -----------------------------------------------------------------------------

@router.delete("/{contact_pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_pk: int, db: Session = Depends(get_db)) -> None:
    contact = get_or_404(db, Contact, contact_pk, _LABEL)
    db.delete(contact)
    commit(db, Contact, _LABEL)


# -----------------------------------------------------------------------------

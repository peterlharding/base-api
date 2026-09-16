#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for note, served under /api/v1/notes.

The path parameter is the surrogate key ``id``.  The ``guid`` column is an
ordinary field on the model.

``parent_type`` / ``parent_id`` form a polymorphic reference to the owning
record.  Neither is constrained: the CRM tables declare no foreign keys,
so nothing here validates the pair.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import Note
from app.db.session  import get_db


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/notes", tags=["notes"])

_LABEL = "note"


# -----------------------------------------------------------------------------

@router.get("", response_model=list[schemas.Note])
def list_notes(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Note]:
    """Page through note in id order."""
    stmt = select(Note).order_by(Note.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post("", response_model=schemas.Note, status_code=status.HTTP_201_CREATED)
def create_note(payload: schemas.NoteCreate, db: Session = Depends(get_db)) -> Note:
    note = Note(**payload.model_dump(exclude_unset=True))
    db.add(note)
    commit(db, Note, _LABEL)
    db.refresh(note)
    return note


# -----------------------------------------------------------------------------

@router.get("/{note_pk}", response_model=schemas.Note)
def get_note(note_pk: int, db: Session = Depends(get_db)) -> Note:
    """Fetch a single note by surrogate key."""
    return get_or_404(db, Note, note_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put("/{note_pk}", response_model=schemas.Note)
def update_note(
    note_pk: int,
    payload: schemas.NoteUpdate,
    db: Session = Depends(get_db),
) -> Note:
    """Patch a note: only the fields present in the payload are changed."""
    note = get_or_404(db, Note, note_pk, _LABEL)
    apply_update(note, payload.model_dump(exclude_unset=True))
    commit(db, Note, _LABEL)
    db.refresh(note)
    return note


# -----------------------------------------------------------------------------

@router.delete("/{note_pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_pk: int, db: Session = Depends(get_db)) -> None:
    note = get_or_404(db, Note, note_pk, _LABEL)
    db.delete(note)
    commit(db, Note, _LABEL)


# -----------------------------------------------------------------------------

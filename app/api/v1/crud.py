#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""Helpers shared by the version 1 endpoint modules.

Every resource follows the same shape - page, create, fetch-or-404,
patch-style update, delete - so the parts that differ only by model live here
rather than being repeated per resource.
"""
# -----------------------------------------------------------------------------

from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import Base


# -----------------------------------------------------------------------------

ModelT = TypeVar("ModelT", bound=Base)


# -----------------------------------------------------------------------------
# Postgres SQLSTATEs worth translating into a 4xx.  psycopg exposes the code on
# IntegrityError.orig.sqlstate; without this the violation escapes as a 500.

_UNIQUE_VIOLATION      = "23505"
_FOREIGN_KEY_VIOLATION = "23503"
_NOT_NULL_VIOLATION    = "23502"
_CHECK_VIOLATION       = "23514"


# -----------------------------------------------------------------------------

def _conflict_field(exc: IntegrityError, table: str) -> str | None:
    """Best-effort name of the field behind a unique violation.

    Postgres reports the constraint (``application_user_email_key``) but leaves
    ``diag.column_name`` empty for unique violations, so the field is derived
    from the constraint name rather than read off the error.
    """
    diag = getattr(exc.orig, "diag", None)
    name = getattr(diag, "constraint_name", None)
    if not name:
        return None
    name = name.removeprefix(f"{table}_")
    return name.removesuffix("_key") or None


# -----------------------------------------------------------------------------

def _stamp(db: Session, actor_id: int | None) -> None:
    """Record who is writing, on the rows about to be written.

    Applied here rather than in each endpoint because every write already
    funnels through commit(), so there is one place to get it right and no
    route can quietly skip it.

    Only tables that carry the columns are touched - access, audit_log and
    login_session do not have them.  created_by_id is set once, on insert;
    updated_by_id on every write.  Neither is exposed on the write schemas,
    so a client cannot claim to be someone else: the value comes from the
    bearer token or not at all.
    """
    if actor_id is None:
        return

    for obj in db.new:
        columns = obj.__table__.columns
        if "created_by_id" in columns and obj.created_by_id is None:
            obj.created_by_id = actor_id
        if "updated_by_id" in columns:
            obj.updated_by_id = actor_id

    for obj in db.dirty:
        if "updated_by_id" in obj.__table__.columns:
            obj.updated_by_id = actor_id


# -----------------------------------------------------------------------------

def commit(db: Session, model: type[ModelT], label: str, actor_id: int | None) -> None:
    """Commit, turning constraint violations into 4xx instead of a 500.

    The session is rolled back first: after an IntegrityError the transaction
    is aborted, and any later use of the session would fail too.

    ``actor_id`` is required rather than defaulted, so a new endpoint that
    forgets it fails loudly at import rather than silently writing rows with
    no provenance.  Pass None only where there genuinely is no actor.
    """
    _stamp(db, actor_id)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        sqlstate = getattr(exc.orig, "sqlstate", None)

        if sqlstate == _UNIQUE_VIOLATION:
            field = _conflict_field(exc, model.__tablename__)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"A {label} with this {field} already exists" if field
                    else "That value is already taken"
                ),
            ) from exc

        if sqlstate in (_FOREIGN_KEY_VIOLATION, _NOT_NULL_VIOLATION, _CHECK_VIOLATION):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The request violates a database constraint",
            ) from exc

        raise


# -----------------------------------------------------------------------------

def get_or_404(db: Session, model: type[ModelT], pk: int, label: str) -> ModelT:
    """Fetch by surrogate key, or raise 404."""
    row = db.get(model, pk)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{label.capitalize()} {pk} not found",
        )
    return row


# -----------------------------------------------------------------------------

def apply_update(row: ModelT, fields: dict) -> ModelT:
    """Apply a patch-style payload; an empty payload is a 400."""
    if not fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update",
        )
    for name, value in fields.items():
        setattr(row, name, value)
    return row


# -----------------------------------------------------------------------------

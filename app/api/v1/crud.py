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

def _describe(obj, changed: list[str] | None) -> str:
    """A short summary of what a write did.

    For an update, the columns that actually changed - which is the question
    someone reading the log will have.  Values are deliberately not recorded:
    an audit table holding old and new values of every column becomes a second
    copy of the database, including the parts nobody wanted duplicated.
    """
    if changed:
        return "changed: " + ", ".join(sorted(changed))
    return ""


# -----------------------------------------------------------------------------

def _audit(db: Session, actor_guid: str | None) -> list:
    """Build audit entries for whatever this session is about to write.

    Read from the session rather than passed in by each endpoint, for the same
    reason the stamps are: a route that forgets to call it is silently
    unaudited, and nothing says so.

    Recording what the session actually changed, rather than the HTTP method,
    means a PUT that alters nothing produces no entry - the log describes the
    data, not the request.

    Must run before the flush: SQLAlchemy discards attribute history once the
    change is written, so the changed-column names are only available now.
    Row ids for inserts are only available after, which is why this returns
    thunks rather than finished rows.
    """
    from sqlalchemy import inspect as sa_inspect

    from app.core.config import get_settings
    from app.models import AuditLog

    if actor_guid is None:
        return []

    application = get_settings().app_name
    pending = []

    def _plan(obj, action, changed=None):
        if isinstance(obj, AuditLog):
            return                              # do not audit the audit trail
        pending.append((obj, action, _describe(obj, changed)))

    for obj in db.new:
        _plan(obj, "create")

    for obj in db.dirty:
        if not db.is_modified(obj):
            continue                            # touched but unchanged
        changed = [
            name for name, attr in sa_inspect(obj).attrs.items()
            if attr.history.has_changes()
        ]
        _plan(obj, "update", changed)

    for obj in db.deleted:
        _plan(obj, "delete")

    def _build() -> list:
        # after the flush, so an inserted row knows its id
        return [
            AuditLog(
                application=application,
                action=action,
                reference_type=obj.__tablename__,
                reference_id=getattr(obj, "id", None),
                description=description,
                user_id=actor_guid,
            )
            for obj, action, description in pending
        ]

    return [_build] if pending else []


# -----------------------------------------------------------------------------

def commit(
    db: Session,
    model: type[ModelT],
    label: str,
    actor_id: int | None,
    actor_guid: str | None = None,
) -> None:
    """Commit, turning constraint violations into 4xx instead of a 500.

    The session is rolled back first: after an IntegrityError the transaction
    is aborted, and any later use of the session would fail too.

    ``actor_id`` is required rather than defaulted, so a new endpoint that
    forgets it fails loudly at import rather than silently writing rows with
    no provenance.  Pass None only where there genuinely is no actor.

    ``actor_guid`` is what audit_log records.  Without it the write still
    happens and is still stamped, but leaves no audit entry - so it is
    defaulted rather than required, and endpoints pass ``actor.guid``.
    """
    _stamp(db, actor_id)
    deferred = _audit(db, actor_guid)

    try:
        if deferred:
            db.flush()                          # assigns ids to inserted rows
            for build in deferred:
                db.add_all(build())
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

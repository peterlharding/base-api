#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for event, served under /api/v1/events.

The path parameter is the surrogate key ``id``.  The ``guid`` column is an
ordinary field on the model.

``guid``, ``who_ref`` and ``what_ref`` are 18-character Salesforce-style
ids.  Note that ``account_id`` and ``owner_id`` are **varchar(18) on this
table**, not bigint as they are elsewhere, so the schema types them as
strings to match.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import Event
from app.db.session  import get_db
from app.auth.bearer import jwt_bearer


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/events", tags=["events"])

_LABEL = "event"


# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[schemas.Event],
    dependencies=[Depends(jwt_bearer)]
)
def list_events(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Event]:
    """Page through event in id order."""
    stmt = select(Event).order_by(Event.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post(
    "",
    response_model=schemas.Event,
    dependencies=[Depends(jwt_bearer)],
    status_code=status.HTTP_201_CREATED
)
def create_event(payload: schemas.EventCreate, db: Session = Depends(get_db)) -> Event:
    event = Event(**payload.model_dump(exclude_unset=True))
    db.add(event)
    commit(db, Event, _LABEL)
    db.refresh(event)
    return event


# -----------------------------------------------------------------------------

@router.get(
    "/{event_pk}",
    response_model=schemas.Event,
    dependencies=[Depends(jwt_bearer)]
)
def get_event(event_pk: int, db: Session = Depends(get_db)) -> Event:
    """Fetch a single event by surrogate key."""
    return get_or_404(db, Event, event_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put(
    "/{event_pk}",
    response_model=schemas.Event,
    dependencies=[Depends(jwt_bearer)]
)
def update_event(
    event_pk: int,
    payload: schemas.EventUpdate,
    db: Session = Depends(get_db),
) -> Event:
    """Patch a event: only the fields present in the payload are changed."""
    event = get_or_404(db, Event, event_pk, _LABEL)
    apply_update(event, payload.model_dump(exclude_unset=True))
    commit(db, Event, _LABEL)
    db.refresh(event)
    return event


# -----------------------------------------------------------------------------

@router.delete(
    "/{event_pk}",
    dependencies=[Depends(jwt_bearer)],
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_event(event_pk: int, db: Session = Depends(get_db)) -> None:
    event = get_or_404(db, Event, event_pk, _LABEL)
    db.delete(event)
    commit(db, Event, _LABEL)


# -----------------------------------------------------------------------------

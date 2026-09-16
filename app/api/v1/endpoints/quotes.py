#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for quote, served under /api/v1/quotes.

The path parameter is the surrogate key ``id``.

``quoter`` is NOT NULL in the database, so it is mandatory on create - the
only resource where the required field comes from the schema rather than an
API-level choice.  The money columns are ``numeric(12, 2)`` and serialise as
JSON strings to avoid float rounding.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import Quote
from app.db.session  import get_db


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/quotes", tags=["quotes"])

_LABEL = "quote"


# -----------------------------------------------------------------------------

@router.get("", response_model=list[schemas.Quote])
def list_quotes(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Quote]:
    """Page through quote in id order."""
    stmt = select(Quote).order_by(Quote.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post("", response_model=schemas.Quote, status_code=status.HTTP_201_CREATED)
def create_quote(payload: schemas.QuoteCreate, db: Session = Depends(get_db)) -> Quote:
    row = Quote(**payload.model_dump(exclude_unset=True))
    db.add(row)
    commit(db, Quote, _LABEL)
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.get("/{quote_pk}", response_model=schemas.Quote)
def get_quote(quote_pk: int, db: Session = Depends(get_db)) -> Quote:
    """Fetch a single quote by surrogate key."""
    return get_or_404(db, Quote, quote_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put("/{quote_pk}", response_model=schemas.Quote)
def update_quote(
    quote_pk: int,
    payload: schemas.QuoteUpdate,
    db: Session = Depends(get_db),
) -> Quote:
    """Patch a quote: only the fields present in the payload are changed."""
    row = get_or_404(db, Quote, quote_pk, _LABEL)
    apply_update(row, payload.model_dump(exclude_unset=True))
    commit(db, Quote, _LABEL)
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.delete("/{quote_pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quote(quote_pk: int, db: Session = Depends(get_db)) -> None:
    row = get_or_404(db, Quote, quote_pk, _LABEL)
    db.delete(row)
    commit(db, Quote, _LABEL)


# -----------------------------------------------------------------------------

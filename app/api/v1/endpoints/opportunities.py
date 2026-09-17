#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for opportunity, served under /api/v1/opportunities.

The path parameter is the surrogate key ``id``.

``account_id``, ``owner_id``, ``campaign_ref`` and ``pricebook_ref`` are
unconstrained: the CRM tables declare no foreign keys, so nothing here
validates that they point at an existing row.  The money columns
(``amount``, ``expected_revenue``, ``probability``) are varchar on this
table, not numeric, so they are typed as strings.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import ApplicationUser, Opportunity
from app.db.session  import get_db
from app.auth.bearer import jwt_bearer


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

_LABEL = "opportunity"


# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[schemas.Opportunity],
    dependencies=[Depends(jwt_bearer)]
)
def list_opportunities(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Opportunity]:
    """Page through opportunity in id order."""
    stmt = select(Opportunity).order_by(Opportunity.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post(
    "",
    response_model=schemas.Opportunity,
    status_code=status.HTTP_201_CREATED
)
def create_opportunity(payload: schemas.OpportunityCreate, db: Session = Depends(get_db), actor: ApplicationUser = Depends(jwt_bearer)) -> Opportunity:
    row = Opportunity(**payload.model_dump(exclude_unset=True))
    db.add(row)
    commit(db, Opportunity, _LABEL, actor.id, str(actor.guid))
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.get(
    "/{opportunity_pk}",
    response_model=schemas.Opportunity,
    dependencies=[Depends(jwt_bearer)]
)
def get_opportunity(opportunity_pk: int, db: Session = Depends(get_db)) -> Opportunity:
    """Fetch a single opportunity by surrogate key."""
    return get_or_404(db, Opportunity, opportunity_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put(
    "/{opportunity_pk}",
    response_model=schemas.Opportunity,
)
def update_opportunity(
    opportunity_pk: int,
    payload: schemas.OpportunityUpdate,
    db: Session = Depends(get_db),
    actor: ApplicationUser = Depends(jwt_bearer),
) -> Opportunity:
    """Patch a opportunity: only the fields present in the payload are changed."""
    row = get_or_404(db, Opportunity, opportunity_pk, _LABEL)
    apply_update(row, payload.model_dump(exclude_unset=True))
    commit(db, Opportunity, _LABEL, actor.id, str(actor.guid))
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.delete(
    "/{opportunity_pk}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_opportunity(opportunity_pk: int, db: Session = Depends(get_db), actor: ApplicationUser = Depends(jwt_bearer)) -> None:
    row = get_or_404(db, Opportunity, opportunity_pk, _LABEL)
    db.delete(row)
    commit(db, Opportunity, _LABEL, actor.id, str(actor.guid))


# -----------------------------------------------------------------------------

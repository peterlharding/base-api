#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for lead, served under /api/v1/leads.

The path parameter is the surrogate key ``id``.

``converted_account_id`` / ``converted_contact_id`` /
``converted_opportunity_id`` record what a lead became once ``is_converted``
is set.  None of them are constrained, and nothing here enforces that they
are populated together or that ``is_converted`` agrees with them.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import ApplicationUser, Lead
from app.db.session  import get_db
from app.auth.bearer import jwt_bearer


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/leads", tags=["leads"])

_LABEL = "lead"


# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[schemas.Lead],
    dependencies=[Depends(jwt_bearer)]
)
def list_leads(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Lead]:
    """Page through lead in id order."""
    stmt = select(Lead).order_by(Lead.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post(
    "",
    response_model=schemas.Lead,
    status_code=status.HTTP_201_CREATED
)
def create_lead(payload: schemas.LeadCreate, db: Session = Depends(get_db), actor: ApplicationUser = Depends(jwt_bearer)) -> Lead:
    row = Lead(**payload.model_dump(exclude_unset=True))
    db.add(row)
    commit(db, Lead, _LABEL, actor.id, str(actor.guid))
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.get(
    "/{lead_pk}",
    response_model=schemas.Lead,
    dependencies=[Depends(jwt_bearer)]
)
def get_lead(lead_pk: int, db: Session = Depends(get_db)) -> Lead:
    """Fetch a single lead by surrogate key."""
    return get_or_404(db, Lead, lead_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put(
    "/{lead_pk}",
    response_model=schemas.Lead,
)
def update_lead(
    lead_pk: int,
    payload: schemas.LeadUpdate,
    db: Session = Depends(get_db),
    actor: ApplicationUser = Depends(jwt_bearer),
) -> Lead:
    """Patch a lead: only the fields present in the payload are changed."""
    row = get_or_404(db, Lead, lead_pk, _LABEL)
    apply_update(row, payload.model_dump(exclude_unset=True))
    commit(db, Lead, _LABEL, actor.id, str(actor.guid))
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.delete(
    "/{lead_pk}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_lead(lead_pk: int, db: Session = Depends(get_db), actor: ApplicationUser = Depends(jwt_bearer)) -> None:
    row = get_or_404(db, Lead, lead_pk, _LABEL)
    db.delete(row)
    commit(db, Lead, _LABEL, actor.id, str(actor.guid))


# -----------------------------------------------------------------------------

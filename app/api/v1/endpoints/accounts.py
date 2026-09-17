#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for account, served under /api/v1/accounts.

The path parameter is the surrogate key ``id``.  The ``guid`` column (a
client-side uuid) is an ordinary field on the model.

``parent_id`` and ``owner_id`` are plain bigints: the CRM tables declare no
foreign keys, so nothing here validates that they point at an existing row,
and ``parent_id`` is not checked for cycles.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import Account
from app.db.session  import get_db
from app.auth.bearer import jwt_bearer


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/accounts", tags=["accounts"])

_LABEL = "account"


# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[schemas.Account],
    dependencies=[Depends(jwt_bearer)]
)
def list_accounts(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Account]:
    """Page through account in id order."""
    stmt = select(Account).order_by(Account.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post(
    "",
    response_model=schemas.Account,
    dependencies=[Depends(jwt_bearer)],
    status_code=status.HTTP_201_CREATED
)
def create_account(payload: schemas.AccountCreate, db: Session = Depends(get_db)) -> Account:
    account = Account(**payload.model_dump(exclude_unset=True))
    db.add(account)
    commit(db, Account, _LABEL)
    db.refresh(account)
    return account


# -----------------------------------------------------------------------------

@router.get(
    "/{account_pk}",
    response_model=schemas.Account,
    dependencies=[Depends(jwt_bearer)]
)
def get_account(account_pk: int, db: Session = Depends(get_db)) -> Account:
    """Fetch a single account by surrogate key."""
    return get_or_404(db, Account, account_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put(
    "/{account_pk}",
    response_model=schemas.Account,
    dependencies=[Depends(jwt_bearer)]
)
def update_account(
    account_pk: int,
    payload: schemas.AccountUpdate,
    db: Session = Depends(get_db),
) -> Account:
    """Patch an account: only the fields present in the payload are changed."""
    account = get_or_404(db, Account, account_pk, _LABEL)
    apply_update(account, payload.model_dump(exclude_unset=True))
    commit(db, Account, _LABEL)
    db.refresh(account)
    return account


# -----------------------------------------------------------------------------

@router.delete(
    "/{account_pk}",
    dependencies=[Depends(jwt_bearer)],
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_account(account_pk: int, db: Session = Depends(get_db)) -> None:
    account = get_or_404(db, Account, account_pk, _LABEL)
    db.delete(account)
    commit(db, Account, _LABEL)


# -----------------------------------------------------------------------------

#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for user_role, served under /api/v1/user-roles.

The path parameter is the surrogate key ``id``.  The route is kebab-cased
because it is the first resource whose name is two words; the module, the
table and the model stay snake_case.

``parent_role_id`` is a self-reference forming the role hierarchy, and
``forecast_user_id`` points at application_user.  Both carry foreign keys
(migration 0004) with ON DELETE SET NULL, so deleting a parent role flattens
its children rather than removing them.  Nothing here checks the hierarchy
for cycles.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import UserRole
from app.db.session  import get_db
from app.auth.bearer import jwt_bearer


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/user-roles", tags=["user-roles"])

_LABEL = "user role"


# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[schemas.UserRole],
    dependencies=[Depends(jwt_bearer)]
)
def list_user_roles(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[UserRole]:
    """Page through user_role in id order."""
    stmt = select(UserRole).order_by(UserRole.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post(
    "",
    response_model=schemas.UserRole,
    dependencies=[Depends(jwt_bearer)],
    status_code=status.HTTP_201_CREATED
)
def create_user_role(
    payload: schemas.UserRoleCreate,
    db: Session = Depends(get_db),
) -> UserRole:
    row = UserRole(**payload.model_dump(exclude_unset=True))
    db.add(row)
    commit(db, UserRole, _LABEL)
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.get(
    "/{user_role_pk}",
    response_model=schemas.UserRole,
    dependencies=[Depends(jwt_bearer)]
)
def get_user_role(user_role_pk: int, db: Session = Depends(get_db)) -> UserRole:
    """Fetch a single user role by surrogate key."""
    return get_or_404(db, UserRole, user_role_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put(
    "/{user_role_pk}",
    response_model=schemas.UserRole,
    dependencies=[Depends(jwt_bearer)]
)
def update_user_role(
    user_role_pk: int,
    payload: schemas.UserRoleUpdate,
    db: Session = Depends(get_db),
) -> UserRole:
    """Patch a user role: only the fields present in the payload are changed."""
    row = get_or_404(db, UserRole, user_role_pk, _LABEL)
    apply_update(row, payload.model_dump(exclude_unset=True))
    commit(db, UserRole, _LABEL)
    db.refresh(row)
    return row


# -----------------------------------------------------------------------------

@router.delete(
    "/{user_role_pk}",
    dependencies=[Depends(jwt_bearer)],
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_user_role(user_role_pk: int, db: Session = Depends(get_db)) -> None:
    row = get_or_404(db, UserRole, user_role_pk, _LABEL)
    db.delete(row)
    commit(db, UserRole, _LABEL)


# -----------------------------------------------------------------------------

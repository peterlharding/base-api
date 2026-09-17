#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for application_user, served under /api/v1/users.

The path parameter is the surrogate key ``id``.  The ``guid`` column (a
client-side GUID) is an ordinary field on the model, not the path parameter.
"""
# -----------------------------------------------------------------------------

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import ApplicationUser
from app.db.session  import get_db
from app.auth.bearer import jwt_bearer


# -----------------------------------------------------------------------------

# Every route here requires a bearer token.  The shared jwt_bearer instance
# is used rather than Depends(JWTBearer()): a fresh instance per route cannot
# be reached by app.dependency_overrides, which makes the routes untestable
# without minting a real token for every case.
router = APIRouter(prefix="/users", tags=["users"])

_LABEL = "user"


# -----------------------------------------------------------------------------

@router.get("",
           response_model=list[schemas.User],
           dependencies=[Depends(jwt_bearer)])
def list_users(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ApplicationUser]:
    """Page through application_user in id order."""
    stmt = select(ApplicationUser).order_by(ApplicationUser.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post("",
             response_model=schemas.User,
             dependencies=[Depends(jwt_bearer)],
             status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)) -> ApplicationUser:
    user = ApplicationUser(**payload.model_dump(exclude_unset=True))
    db.add(user)
    commit(db, ApplicationUser, _LABEL)
    db.refresh(user)
    return user


# -----------------------------------------------------------------------------

@router.get("/{user_pk}",
            response_model=schemas.User,
            dependencies=[Depends(jwt_bearer)])
def get_user(user_pk: int, db: Session = Depends(get_db)) -> ApplicationUser:
    """Fetch a single user by surrogate key."""
    return get_or_404(db, ApplicationUser, user_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put("/{user_pk}",
            response_model=schemas.User,
            dependencies=[Depends(jwt_bearer)])
def update_user(
    user_pk: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
) -> ApplicationUser:
    """Patch a user: only the fields present in the payload are changed."""
    user = get_or_404(db, ApplicationUser, user_pk, _LABEL)
    apply_update(user, payload.model_dump(exclude_unset=True))
    commit(db, ApplicationUser, _LABEL)
    db.refresh(user)
    return user


# -----------------------------------------------------------------------------

@router.delete("/{user_pk}",
                status_code=status.HTTP_204_NO_CONTENT,
                dependencies=[Depends(jwt_bearer)])
def delete_user(user_pk: int, db: Session = Depends(get_db)) -> None:
    user = get_or_404(db, ApplicationUser, user_pk, _LABEL)
    db.delete(user)
    commit(db, ApplicationUser, _LABEL)


# -----------------------------------------------------------------------------

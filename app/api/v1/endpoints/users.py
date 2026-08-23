#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for application_user, served under /api/v1/users.

The path parameter is ``id`` — the surrogate key of the table. The legacy
``user_id`` column (a client-side string) is an ordinary field on the model.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1 import schemas
from app.db.models import ApplicationUser
from app.db.session import get_db


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/users", tags=["users"])


# -----------------------------------------------------------------------------

def _get_or_404(db: Session, user_id: int) -> ApplicationUser:
    user = db.get(ApplicationUser, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return user


# -----------------------------------------------------------------------------

@router.get("", response_model=list[schemas.User])
def list_users(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ApplicationUser]:
    """Page through application_user in id order."""
    stmt = select(ApplicationUser).order_by(ApplicationUser.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post("", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)) -> ApplicationUser:
    user = ApplicationUser(**payload.model_dump(exclude_unset=True))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# -----------------------------------------------------------------------------

@router.get("/{user_pk}", response_model=schemas.User)
def get_user(user_pk: int, db: Session = Depends(get_db)) -> ApplicationUser:
    """Fetch a single user by surrogate key."""
    return _get_or_404(db, user_pk)


# -----------------------------------------------------------------------------

@router.put("/{user_pk}", response_model=schemas.User)
def update_user(
    user_pk: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
) -> ApplicationUser:
    """Patch a user: only the fields present in the payload are changed."""
    user = _get_or_404(db, user_pk)
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update",
        )
    for name, value in fields.items():
        setattr(user, name, value)
    db.commit()
    db.refresh(user)
    return user


# -----------------------------------------------------------------------------

@router.delete("/{user_pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_pk: int, db: Session = Depends(get_db)) -> None:
    user = _get_or_404(db, user_pk)
    db.delete(user)
    db.commit()


# -----------------------------------------------------------------------------

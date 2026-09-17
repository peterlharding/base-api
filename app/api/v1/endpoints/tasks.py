#!/usr/bin/env python
#
# -----------------------------------------------------------------------------
"""CRUD endpoints for task, served under /api/v1/tasks.

The path parameter is the surrogate key ``id``.  The ``guid`` column is an
ordinary field on the model.

``who_id`` / ``what_id`` form a polymorphic reference alongside the
``who_type`` / ``what_type`` discriminators, and ``owner_id`` and
``account_id`` are plain bigints: the CRM tables declare no foreign keys,
so nothing here validates that any of them point at an existing row.
"""
# -----------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session


# -----------------------------------------------------------------------------

from app.api.v1      import schemas
from app.api.v1.crud import apply_update, commit, get_or_404
from app.models      import ApplicationUser, Task
from app.db.session  import get_db
from app.auth.bearer import jwt_bearer


# -----------------------------------------------------------------------------

router = APIRouter(prefix="/tasks", tags=["tasks"])

_LABEL = "task"


# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[schemas.Task],
    dependencies=[Depends(jwt_bearer)]
)
def list_tasks(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Task]:
    """Page through task in id order."""
    stmt = select(Task).order_by(Task.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


# -----------------------------------------------------------------------------

@router.post(
    "",
    response_model=schemas.Task,
    status_code=status.HTTP_201_CREATED
)
def create_task(payload: schemas.TaskCreate, db: Session = Depends(get_db), actor: ApplicationUser = Depends(jwt_bearer)) -> Task:
    task = Task(**payload.model_dump(exclude_unset=True))
    db.add(task)
    commit(db, Task, _LABEL, actor.id)
    db.refresh(task)
    return task


# -----------------------------------------------------------------------------

@router.get(
    "/{task_pk}",
    response_model=schemas.Task,
    dependencies=[Depends(jwt_bearer)]
)
def get_task(task_pk: int, db: Session = Depends(get_db)) -> Task:
    """Fetch a single task by surrogate key."""
    return get_or_404(db, Task, task_pk, _LABEL)


# -----------------------------------------------------------------------------

@router.put(
    "/{task_pk}",
    response_model=schemas.Task,
)
def update_task(
    task_pk: int,
    payload: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    actor: ApplicationUser = Depends(jwt_bearer),
) -> Task:
    """Patch a task: only the fields present in the payload are changed."""
    task = get_or_404(db, Task, task_pk, _LABEL)
    apply_update(task, payload.model_dump(exclude_unset=True))
    commit(db, Task, _LABEL, actor.id)
    db.refresh(task)
    return task


# -----------------------------------------------------------------------------

@router.delete(
    "/{task_pk}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_task(task_pk: int, db: Session = Depends(get_db), actor: ApplicationUser = Depends(jwt_bearer)) -> None:
    task = get_or_404(db, Task, task_pk, _LABEL)
    db.delete(task)
    commit(db, Task, _LABEL, actor.id)


# -----------------------------------------------------------------------------

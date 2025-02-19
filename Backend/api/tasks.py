from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from Backend.data_layer.database.connection import get_db
from Backend.data_layer.database.models.task import Task, TaskStatus
from Backend.app.schemas.task_schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskWithDetails
)
from Backend.data_layer.database.models.task_history import TaskHistory
from Backend.api.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_task = Task(
        title=task.title,
        description=task.description,
        status=TaskStatus.TODO,
        creator_id=current_user.id,
        assignee_id=task.assignee_id,
        priority=task.priority,
        category_id=task.category_id,
        project_id=task.project_id,
        organization_id=current_user.organization_id,
        due_date=task.due_date
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/{task_id}", response_model=TaskWithDetails)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TaskStatus] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Task).filter(
        Task.organization_id == current_user.organization_id)
    if status:
        query = query.filter(Task.status == status)
    return query.offset(skip).limit(limit).all()


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update task fields
    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(db_task, field, value)

    # Record task history
    history = TaskHistory(
        task_id=task_id,
        user_id=current_user.id,
        action="update",
        field="multiple",
        new_value=str(task_update.dict(exclude_unset=True))
    )
    db.add(history)

    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}

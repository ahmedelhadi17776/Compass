from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.data.database.connection import get_db
from src.services.authentication.auth_service import get_current_user
from src.application.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from src.services.task_service.task_manager import TaskManager

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new task."""
    task_manager = TaskManager(db)
    return await task_manager.create_task(task, current_user.id)

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tasks for the current user."""
    task_manager = TaskManager(db)
    return await task_manager.get_user_tasks(current_user.id)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific task by ID."""
    task_manager = TaskManager(db)
    task = await task_manager.get_task(task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a task."""
    task_manager = TaskManager(db)
    updated_task = await task_manager.update_task(task_id, task_update, current_user.id)
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return updated_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a task."""
    task_manager = TaskManager(db)
    success = await task_manager.delete_task(task_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return None

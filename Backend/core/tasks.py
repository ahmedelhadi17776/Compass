from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from Backend.data.database.connection import get_db
from Backend.services.authentication.auth_service import get_current_user
from Backend.application.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from Backend.services.task_service.task_service import TaskService
from Backend.data.repositories.task_repository import TaskRepository

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
    task_repository = TaskRepository(db)
    task_service = TaskService(task_repository)
    return await task_service.create_task(task, current_user.id)

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = Query(None, description="Filter tasks by status"),
    priority: Optional[str] = Query(None, description="Filter tasks by priority"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tasks for the current user."""
    task_repository = TaskRepository(db)
    task_service = TaskService(task_repository)
    
    if status:
        return await task_service.get_tasks_by_status(current_user.id, status)
    elif priority:
        return await task_service.get_tasks_by_priority(current_user.id, priority)
    return await task_service.get_user_tasks(current_user.id)

@router.get("/overdue", response_model=List[TaskResponse])
async def get_overdue_tasks(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overdue tasks."""
    task_repository = TaskRepository(db)
    task_service = TaskService(task_repository)
    return await task_service.get_overdue_tasks(current_user.id)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific task by ID."""
    task_repository = TaskRepository(db)
    task_service = TaskService(task_repository)
    task = await task_service.get_task(task_id, current_user.id)
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
    task_repository = TaskRepository(db)
    task_service = TaskService(task_repository)
    updated_task = await task_service.update_task(task_id, current_user.id, task_update)
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
    task_repository = TaskRepository(db)
    task_service = TaskService(task_repository)
    success = await task_service.delete_task(task_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return None

@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a task as complete."""
    task_repository = TaskRepository(db)
    task_service = TaskService(task_repository)
    task = await task_service.mark_task_complete(task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task

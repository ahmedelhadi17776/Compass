from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime

from Backend.data_layer.database.connection import get_db
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority
from Backend.app.schemas.task_schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskWithDetails
)
from Backend.data_layer.database.models.task_history import TaskHistory
from Backend.services.task_service import TaskService
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.api.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new task."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    result = await service.create_task(
        title=task.title,
        description=task.description,
        creator_id=current_user.id,
        project_id=task.project_id,
        organization_id=task.organization_id,
        workflow_id=task.workflow_id,
        assignee_id=task.assignee_id,
        reviewer_id=task.reviewer_id,
        priority=task.priority,
        category_id=task.category_id,
        parent_task_id=task.parent_task_id,
        estimated_hours=task.estimated_hours,
        due_date=task.due_date
    )
    return result


@router.get("/{task_id}", response_model=TaskWithDetails)
async def get_task(
    task_id: int,
    include_metrics: bool = Query(
        False, description="Include task metrics in response"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get task details with optional metrics."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    task = await service.get_task_with_details(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Convert to Pydantic model
    task_response = TaskWithDetails.from_orm(task)

    if include_metrics:
        metrics = await service.get_task_metrics(task_id)
        if metrics:
            task_response = TaskWithDetails(
                **{**task_response.dict(), "metrics": metrics})

    return task_response


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get tasks with optional filtering."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    if project_id:
        tasks = await repo.get_tasks_by_project(
            project_id=project_id,
            skip=skip,
            limit=limit,
            status=status
        )
    else:
        # TODO: Implement get_tasks with more filters
        tasks = []

    return tasks


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update a task."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    result = await service.update_task(
        task_id=task_id,
        title=task_update.title,
        description=task_update.description,
        status=task_update.status,
        assignee_id=task_update.assignee_id,
        reviewer_id=task_update.reviewer_id,
        priority=task_update.priority,
        category_id=task_update.category_id,
        due_date=task_update.due_date,
        actual_hours=task_update.actual_hours,
        progress_metrics=task_update.progress_metrics,
        blockers=task_update.blockers,
        user_id=current_user.id
    )

    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Delete a task."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    success = await repo.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}


@router.get("/{task_id}/history", response_model=List[TaskHistory])
async def get_task_history(
    task_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get task history entries."""
    repo = TaskRepository(db)
    history = await repo.get_task_history(task_id, skip, limit)
    return history


@router.get("/{task_id}/metrics")
async def get_task_metrics(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get task metrics and analytics."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    metrics = await service.get_task_metrics(task_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Task not found")
    return metrics

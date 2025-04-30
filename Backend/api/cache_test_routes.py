from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional
from Backend.services.task_service import TaskService
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.database.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
import json

router = APIRouter(prefix="/cache-test", tags=["cache-test"])


@router.get("/tasks")
async def get_cached_tasks(
    db: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 10
):
    """Test endpoint to verify task caching in Redis."""
    # Create repository and service
    repo = TaskRepository(db)
    service = TaskService(repo)

    # Get tasks (this should be cached after first call)
    tasks = await service.get_tasks(skip=skip, limit=limit)

    # Convert to dict for JSON response
    task_list = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
            "dependencies": task.dependencies
        }
        task_list.append(task_dict)

    return {
        "message": "This response should be cached in Redis after first call",
        "count": len(task_list),
        "tasks": task_list
    }


@router.get("/task/{task_id}")
async def get_cached_task(task_id: int, db: AsyncSession = Depends(get_db_session)):
    """Test endpoint to verify individual task caching in Redis."""
    # Create repository and service
    repo = TaskRepository(db)
    service = TaskService(repo)

    # Get task (this should be cached after first call)
    task = await service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Convert to dict for JSON response
    task_dict = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "dependencies": task.dependencies
    }

    return {
        "message": "This response should be cached in Redis after first call",
        "task": task_dict
    }

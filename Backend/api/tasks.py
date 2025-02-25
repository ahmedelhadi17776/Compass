from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime

from Backend.data_layer.database.connection import get_db
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority, Task
from Backend.app.schemas.task_schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskWithDetails,
    TaskDependencyUpdate
)
from Backend.data_layer.database.models.task_history import TaskHistory
from Backend.services.task_service import TaskService
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.api.auth import get_current_user
from Backend.ai_services.task_ai.task_classification_service import TaskClassificationService

task_classifier = TaskClassificationService()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new task with AI classification."""
    try:
        # Get AI classification with interaction logging
        ai_analysis = await task_classifier.classify_task(
            task_data={
                "title": task.title,
                "description": task.description,
                "context": {
                    "project_id": task.project_id,
                    "organization_id": task.organization_id
                }
            },
            db_session=db,
            user_id=current_user.id
        )
        
        # Update task data with AI insights
        task_data = task.dict()
        task_data.update({
            "priority": ai_analysis["priority"],
            "estimated_hours": ai_analysis["estimated_hours"],
            "complexity_score": ai_analysis["complexity"],
            "ai_category": ai_analysis["category"],
            "ai_confidence": ai_analysis["confidence"]
        })

        repo = TaskRepository(db)
        service = TaskService(repo)
        result = await service.create_task(**task_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating task: {str(e)}"
        )
@router.post("/{task_id}/ai-analyze")
async def analyze_task_with_ai(
    task_id: int,
    analysis_type: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Analyze task using AI capabilities."""
    repo = TaskRepository(db)
    service = TaskService(repo)
    result = await service.analyze_task_with_ai(task_id, analysis_type)
    return result

@router.post("/{task_id}/agent-interaction")
async def create_task_agent_interaction(
    task_id: int,
    interaction_data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Record a new agent interaction with the task."""
    repo = TaskRepository(db)
    interaction = await repo.create_task_agent_interaction(
        task_id=task_id,
        user_id=current_user.id,
        **interaction_data
    )
    return interaction

@router.get("/{task_id}/agent-interactions")
async def get_task_agent_interactions(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all agent interactions for a task."""
    repo = TaskRepository(db)
    interactions = await repo.get_task_agent_interactions(task_id)
    return interactions

@router.post("/{task_id}/optimize")
async def optimize_task(
    task_id: int,
    optimization_params: Dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Optimize task using AI agents."""
    repo = TaskRepository(db)
    service = TaskService(repo)
    result = await service.optimize_task(task_id, optimization_params)
    return result
@router.put("/{task_id}/dependencies")
async def update_task_dependencies(
    task_id: int,
    dependencies: TaskDependencyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update task dependencies."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    result = await service.update_task_dependencies(task_id, dependencies.dependencies)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Dependencies updated successfully"}


@router.get("/{task_id}/dependencies")
async def get_task_dependencies(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get task dependencies."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    task = await service.get_task_with_details(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Ensure task is a Task object
    if isinstance(task, dict):
        task = Task(**task)  # Convert dict back to Task object if necessary

    dependencies = getattr(task, 'dependencies', None)
    return {"dependencies": dependencies or []}


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
    assignee_id: Optional[int] = None,
    creator_id: Optional[int] = None,
    due_date_start: Optional[datetime] = None,
    due_date_end: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get tasks with optional filtering."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    tasks = await repo.get_tasks_by_project(
        project_id=project_id,
        skip=skip,
        limit=limit,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        creator_id=creator_id,
        due_date_start=due_date_start,
        due_date_end=due_date_end
    ) if project_id else await repo.get_tasks(
        skip=skip,
        limit=limit,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        creator_id=creator_id,
        due_date_start=due_date_start,
        due_date_end=due_date_end
    )

    return tasks
@router.get("/{task_id}/similar", response_model=Dict)
async def get_similar_tasks(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get similar tasks using RAG."""
    repo = TaskRepository(db)
    service = TaskService(repo)
    
    similar_tasks = await service.find_similar_tasks_rag(task_id)
    return similar_tasks
@router.post("/analyze", response_model=Dict)
async def analyze_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Analyze task using AI agents without creating it."""
    try:
        service = TaskService(TaskRepository(db))
        crew_orchestrator = CrewOrchestrator()
        
        analysis = await crew_orchestrator.analyze_and_optimize_task(task_data.dict())
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing task: {str(e)}"
        )
@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
) -> TaskResponse:
    """Update an existing task with status transition validation."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)

        # Get existing task
        existing_task = await service.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        task_data = task_update.dict(exclude_unset=True)

        # Handle status transition if status is being updated
        if 'status' in task_data:
            new_status = TaskStatus(task_data['status'])
            try:
                updated_task = await service.update_task_status(
                    task_id,
                    new_status,
                    current_user.id
                )
                # Remove status from task_data as it's already updated
                task_data.pop('status')
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        # Update remaining fields if any
        if task_data:
            updated_task = await service.update_task(task_id, task_data)

        return TaskResponse.from_orm(updated_task)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating task: {str(e)}"
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Delete a task."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    success = await service.delete_task(task_id)
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

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from Backend.data_layer.database.connection import get_db
from Backend.data_layer.database.models.calendar_event import RecurrenceType
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority, Task
from Backend.app.schemas.task_schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskWithDetails,
    TaskDependencyUpdate,
    TaskHistoryResponse,
    CommentResponse,
    AttachmentResponse
)
from Backend.data_layer.database.models.task_history import TaskHistory
from Backend.services.task_service import TaskService
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.api.auth import get_current_user
from Backend.orchestration.crew_orchestrator import CrewOrchestrator

# Keep only core task operations

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=http_status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Create a new task."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        task_data = task.dict()

        # Validate duration
        if task_data.get("duration") and task_data["duration"] < 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Duration must be positive"
            )

        # Validate recurrence end date
        if task_data.get("recurrence_end_date") and task_data["recurrence_end_date"] < task_data["start_date"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Recurrence end date cannot be before start date"
            )

        result = await service.create_task(**task_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating task: {str(e)}"
        )


@router.get("/by_id/{task_id}", response_model=TaskWithDetails)
async def get_task(
    task_id: int,
    user_id: int,
    include_metrics: bool = Query(
        False, description="Include task metrics in response"),
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get task details with optional metrics."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        task = await service.get_task_with_details(task_id)
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found"
            )
        return task
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving task: {str(e)}"
        )


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    creator_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    duration: Optional[float] = None,
    due_date: Optional[datetime] = None,
    recurrence: Optional[RecurrenceType] = None,
    end_date: Optional[datetime] = None,
    include_recurring: bool = True,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get tasks with optional filtering and calendar support."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)

        # Use service layer's cached method instead of repository
        tasks = await service.get_tasks(
            skip=skip,
            limit=limit,
            status=status,
            priority=priority,
            project_id=project_id,
            assignee_id=assignee_id,
            creator_id=creator_id,
            start_date=start_date,
            duration=duration,
            due_date=due_date,
            recurrence=recurrence,
            end_date=end_date,
            include_recurring=include_recurring
        )

        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tasks: {str(e)}"
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    user_id: int,
    task_update: TaskUpdate,
    update_all_occurrences: bool = Query(
        True, description="Whether to update all occurrences of a recurring task or just this one"),
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
) -> TaskResponse:
    """Update an existing task with status transition validation."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)

        # Get existing task
        existing_task = await service.get_task(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
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
                    user_id
                    # current_user.id
                )
                await service.update_task(task_id, {"status_updated_at": datetime.utcnow()})
                # Remove status from task_data as it's already updated
                task_data.pop('status')
            except Exception as e:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        # Update remaining fields if any
        if task_data:
            updated_task = await service.update_task(task_id, task_data, update_all_occurrences)

        return TaskResponse.from_orm(updated_task)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating task: {str(e)}"
        )


@router.delete("/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Delete a task."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    success = await service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}


@router.get("/{task_id}/history", response_model=List[TaskHistoryResponse])
async def get_task_history(
    task_id: int,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get task history entries."""
    repo = TaskRepository(db)
    history = await repo.get_task_history(task_id, skip, limit)
    return history


@router.get("/{task_id}/metrics")
async def get_task_metrics(
    task_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get task metrics and analytics."""
    repo = TaskRepository(db)
    service = TaskService(repo)

    metrics = await service.get_task_metrics(task_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Task not found")
    return metrics


@router.post("/{task_id}/ai-process", response_model=Dict)
async def process_task_with_ai(
    task_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Process a task using AI agents via CrewOrchestrator.

    This endpoint triggers AI processing on the task, which includes:
    - Task analysis and classification
    - Resource allocation recommendations
    - Timeline optimization
    - Dependency analysis

    Returns:
        Dict: Results of AI processing
    """
    try:
        # Initialize orchestrator
        orchestrator = CrewOrchestrator()

        # Process the task
        results = await orchestrator.process_db_task(task_id)

        if "error" in results:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=results["error"]
            )

        return results
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing task with AI: {str(e)}"
        )


# Task Comment Endpoints
@router.post("/{task_id}/comments", response_model=CommentResponse)
async def create_task_comment(
    task_id: int,
    user_id: int,
    content: str,
    parent_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Create a new comment for a task."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        comment = await service.create_comment(
            task_id=task_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id
        )
        return comment
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating comment: {str(e)}"
        )


@router.get("/{task_id}/comments", response_model=List[CommentResponse])
async def get_task_comments(
    task_id: int,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get all comments for a task."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        comments = await service.get_task_comments(task_id, skip, limit)
        return comments
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving comments: {str(e)}"
        )


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_task_comment(
    comment_id: int,
    user_id: int,
    content: str,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Update a task comment."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        comment = await service.update_comment(comment_id, user_id, content)
        if not comment:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Comment not found or you don't have permission to update it"
            )
        return comment
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating comment: {str(e)}"
        )


@router.delete("/comments/{comment_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_task_comment(
    comment_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Delete a task comment."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        success = await service.delete_comment(comment_id, user_id)
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Comment not found or you don't have permission to delete it"
            )
        return {"message": "Comment deleted successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting comment: {str(e)}"
        )


# Task Category Endpoints
@router.post("/categories", response_model=dict)
async def create_task_category(
    name: str,
    organization_id: int,
    user_id: int,
    description: Optional[str] = None,
    color_code: Optional[str] = None,
    icon: Optional[str] = None,
    parent_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Create a new task category."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        category = await service.create_category(
            name=name,
            organization_id=organization_id,
            description=description,
            color_code=color_code,
            icon=icon,
            parent_id=parent_id
        )
        return {"id": category.id, "name": category.name, "message": "Category created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating category: {str(e)}"
        )


@router.get("/categories", response_model=List[dict])
async def get_task_categories(
    organization_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get all task categories for an organization."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        categories = await service.get_categories(organization_id)
        return [{
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "color_code": cat.color_code,
            "icon": cat.icon,
            "parent_id": cat.parent_id
        } for cat in categories]
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving categories: {str(e)}"
        )


@router.get("/categories/{category_id}", response_model=dict)
async def get_task_category(
    category_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get a task category by ID."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        category = await service.get_category(category_id)
        if not category:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        return {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "color_code": category.color_code,
            "icon": category.icon,
            "parent_id": category.parent_id,
            "organization_id": category.organization_id
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving category: {str(e)}"
        )


@router.put("/categories/{category_id}", response_model=dict)
async def update_task_category(
    category_id: int,
    user_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    color_code: Optional[str] = None,
    icon: Optional[str] = None,
    parent_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Update a task category."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if color_code is not None:
            update_data["color_code"] = color_code
        if icon is not None:
            update_data["icon"] = icon
        if parent_id is not None:
            update_data["parent_id"] = parent_id

        category = await service.update_category(category_id, **update_data)
        if not category:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        return {
            "id": category.id,
            "name": category.name,
            "message": "Category updated successfully"
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating category: {str(e)}"
        )


@router.delete("/categories/{category_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_task_category(
    category_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Delete a task category."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        success = await service.delete_category(category_id)
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        return {"message": "Category deleted successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting category: {str(e)}"
        )


# Task Attachment Endpoints
@router.post("/{task_id}/attachments", response_model=AttachmentResponse)
async def create_task_attachment(
    task_id: int,
    user_id: int,
    file_name: str,
    file_path: str,
    file_type: Optional[str] = None,
    file_size: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Create a new attachment for a task."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        attachment = await service.create_attachment(
            task_id=task_id,
            file_name=file_name,
            file_path=file_path,
            uploaded_by=user_id,
            file_type=file_type,
            file_size=file_size
        )
        return attachment
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating attachment: {str(e)}"
        )


@router.get("/{task_id}/attachments", response_model=List[AttachmentResponse])
async def get_task_attachments(
    task_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get all attachments for a task."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        attachments = await service.get_task_attachments(task_id)
        return attachments
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving attachments: {str(e)}"
        )


@router.delete("/attachments/{attachment_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_task_attachment(
    attachment_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Delete a task attachment."""
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)
        success = await service.delete_attachment(attachment_id, user_id)
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Attachment not found or you don't have permission to delete it"
            )
        return {"message": "Attachment deleted successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting attachment: {str(e)}"
        )


@router.get("/calendar", response_model=List[Dict])
async def get_calendar_tasks(
    start_date: datetime,
    end_date: datetime,
    user_id: int,
    project_id: Optional[int] = None,
    include_recurring: bool = Query(
        True, description="Whether to include recurring tasks and their occurrences"),
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get tasks formatted for calendar view with expanded recurring tasks.

    This endpoint retrieves tasks for a calendar view and expands recurring tasks
    into individual occurrences based on their recurrence pattern.

    Args:
        start_date: Start of the calendar range
        end_date: End of the calendar range
        user_id: User ID for filtering
        project_id: Optional project filter
        expand_recurring: Whether to expand recurring tasks into occurrences

    Returns:
        List of task dictionaries formatted for calendar display
    """
    try:
        repo = TaskRepository(db)
        service = TaskService(repo)

        # Ensure timezone-naive datetime objects
        if start_date.tzinfo:
            start_date = start_date.replace(tzinfo=None)
        if end_date.tzinfo:
            end_date = end_date.replace(tzinfo=None)

        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )

        # Limit range to prevent performance issues (e.g., max 3 months)
        max_range = timedelta(days=90)
        if end_date - start_date > max_range:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Date range too large. Maximum range is {max_range.days} days"
            )

        calendar_tasks = await service.get_calendar_tasks(
            start_date=start_date,
            end_date=end_date,
            project_id=project_id,
            user_id=user_id,
            include_recurring=include_recurring
        )

        return calendar_tasks
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving calendar tasks: {str(e)}"
        )

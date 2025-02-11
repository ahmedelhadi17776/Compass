"""Task service module."""
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.core.security import SecurityContext
from Backend.data.database.models.task import Task
from Backend.data.database.repositories.task_repository import TaskRepository
from Backend.application.schemas.task import TaskCreate, TaskUpdate
from Backend.core.security.exceptions import TaskNotFoundError
from Backend.services.security.security_service import SecurityService
from Backend.core.security.events import SecurityEventType


class TaskService:
    """Task service class."""

    def __init__(self, db: AsyncSession, security_context: SecurityContext):
        """Initialize task service."""
        self.db = db
        self.security_context = security_context
        self.task_repository = TaskRepository(db)
        self.security_service = SecurityService(db, security_context)

    async def create_task(self, task_data: TaskCreate, user_id: int) -> Task:
        """Create a new task."""
        try:
            task_dict = task_data.dict()
            task_dict["user_id"] = user_id
            task = await self.task_repository.create_task(task_dict, user_id)

            await self.security_service.log_security_event(
                event_type=SecurityEventType.TASK_CREATED,
                description=f"Task created: {task.title}",
                metadata={
                    "task_id": task.id,
                    "user_id": self.security_context.user_id
                }
            )

            return task

        except Exception as e:
            await self.security_service.log_security_event(
                event_type=SecurityEventType.ERROR,
                description=f"Task creation failed: {str(e)}",
                metadata={"user_id": self.security_context.user_id}
            )
            raise

    async def get_task(self, task_id: int, user_id: int) -> Task:
        """Get a task by ID."""
        return await self.task_repository.get_task(task_id, user_id)

    async def get_user_tasks(self, user_id: int, status: Optional[str] = None) -> List[Task]:
        """Get all tasks for a user."""
        return await self.task_repository.get_user_tasks(user_id, status)

    async def update_task(self, task_id: int, user_id: int, task_data: TaskUpdate) -> Task:
        """Update a task."""
        try:
            # Verify task exists and user has permission
            task = await self.task_repository.get_by_id(task_id)
            if not task:
                raise TaskNotFoundError(task_id)

            task_dict = task_data.dict(exclude_unset=True)
            updated_task = await self.task_repository.update_task(task_id, user_id, task_dict)

            # Log security event
            await self.security_service.log_security_event(
                event_type=SecurityEventType.TASK_UPDATED,
                description=f"Task updated: {updated_task.title}",
                metadata={
                    "task_id": task_id,
                    "user_id": self.security_context.user_id,
                    "updated_fields": list(task_dict.keys())
                }
            )

            return updated_task

        except Exception as e:
            await self.security_service.log_security_event(
                event_type=SecurityEventType.ERROR,
                description=f"Task update failed: {str(e)}",
                metadata={
                    "task_id": task_id,
                    "user_id": self.security_context.user_id
                }
            )
            raise

    async def delete_task(self, task_id: int, user_id: int) -> None:
        """Delete a task."""
        await self.task_repository.delete_task(task_id, user_id)

    async def get_tasks_by_status(self, user_id: int, status: str) -> List[Task]:
        """Get tasks by status."""
        return await self.task_repository.get_tasks_by_status(user_id, status)

    async def get_tasks_by_priority(self, user_id: int, priority: str) -> List[Task]:
        """Get tasks by priority."""
        return await self.task_repository.get_tasks_by_priority(user_id, priority)

    async def mark_task_complete(self, task_id: int, user_id: int) -> Task:
        """Mark a task as complete."""
        return await self.task_repository.update_task(
            task_id,
            user_id,
            {"status": "completed", "completed_at": datetime.utcnow()}
        )

    async def get_overdue_tasks(self, user_id: int) -> List[Task]:
        """Get overdue tasks."""
        tasks = await self.task_repository.get_user_tasks(user_id, status="pending")
        now = datetime.utcnow()
        return [task for task in tasks if task.due_date and task.due_date < now]

"""Task service module."""
from typing import List, Optional
from datetime import datetime

from src.data.repositories.task_repository import TaskRepository
from src.data.database.models.task import Task
from src.application.schemas.task import TaskCreate, TaskUpdate
from src.core.exceptions import TaskNotFoundError

class TaskService:
    """Task service class."""

    def __init__(self, task_repository: TaskRepository):
        """Initialize task service."""
        self._repository = task_repository

    async def create_task(self, task_data: TaskCreate, user_id: int) -> Task:
        """Create a new task."""
        task_dict = task_data.dict()
        task_dict["user_id"] = user_id
        return await self._repository.create_task(task_dict, user_id)

    async def get_task(self, task_id: int, user_id: int) -> Task:
        """Get a task by ID."""
        return await self._repository.get_task(task_id, user_id)

    async def get_user_tasks(self, user_id: int, status: Optional[str] = None) -> List[Task]:
        """Get all tasks for a user."""
        return await self._repository.get_user_tasks(user_id, status)

    async def update_task(self, task_id: int, user_id: int, task_data: TaskUpdate) -> Task:
        """Update a task."""
        task_dict = task_data.dict(exclude_unset=True)
        return await self._repository.update_task(task_id, user_id, task_dict)

    async def delete_task(self, task_id: int, user_id: int) -> None:
        """Delete a task."""
        await self._repository.delete_task(task_id, user_id)

    async def get_tasks_by_status(self, user_id: int, status: str) -> List[Task]:
        """Get tasks by status."""
        return await self._repository.get_tasks_by_status(user_id, status)

    async def get_tasks_by_priority(self, user_id: int, priority: str) -> List[Task]:
        """Get tasks by priority."""
        return await self._repository.get_tasks_by_priority(user_id, priority)

    async def mark_task_complete(self, task_id: int, user_id: int) -> Task:
        """Mark a task as complete."""
        return await self._repository.update_task(
            task_id,
            user_id,
            {"status": "completed", "completed_at": datetime.utcnow()}
        )

    async def get_overdue_tasks(self, user_id: int) -> List[Task]:
        """Get overdue tasks."""
        tasks = await self._repository.get_user_tasks(user_id, status="pending")
        now = datetime.utcnow()
        return [task for task in tasks if task.due_date and task.due_date < now]

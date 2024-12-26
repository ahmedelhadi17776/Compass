"""Task repository module."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models.task import Task
from ..database.models.user import User
from src.core.exceptions import TaskNotFoundError
class TaskRepository:
    """Task repository class."""

    def __init__(self, session: AsyncSession):
        """Initialize task repository."""
        self._session = session

    async def create_task(self, task_data: dict, user_id: int) -> Task:
        """Create a new task."""
        task = Task(
            title=task_data["title"],
            description=task_data.get("description"),
            due_date=task_data.get("due_date"),
            priority=task_data.get("priority"),
            status=task_data.get("status", "pending"),
            user_id=user_id
        )
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def get_task(self, task_id: int, user_id: int) -> Task:
        """Get a task by ID."""
        task = await self._session.execute(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == user_id
            )
        )
        task = task.scalar_one_or_none()
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")
        return task

    async def get_user_tasks(self, user_id: int, status: Optional[str] = None) -> List[Task]:
        """Get all tasks for a user."""
        query = select(Task).where(Task.user_id == user_id)
        if status:
            query = query.where(Task.status == status)
        tasks = await self._session.execute(query)
        return tasks.scalars().all()

    async def update_task(self, task_id: int, user_id: int, task_data: dict) -> Task:
        """Update a task."""
        task = await self.get_task(task_id, user_id)
        for key, value in task_data.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def delete_task(self, task_id: int, user_id: int) -> None:
        """Delete a task."""
        task = await self.get_task(task_id, user_id)
        await self._session.delete(task)
        await self._session.commit()

    async def get_tasks_by_status(self, user_id: int, status: str) -> List[Task]:
        """Get tasks by status."""
        tasks = await self._session.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.status == status
            )
        )
        return tasks.scalars().all()

    async def get_tasks_by_priority(self, user_id: int, priority: str) -> List[Task]:
        """Get tasks by priority."""
        tasks = await self._session.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.priority == priority
            )
        )
        return tasks.scalars().all()

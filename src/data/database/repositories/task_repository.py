from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.task import Task
from .base_repository import BaseRepository

class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)

    async def get_by_user_id(self, user_id: int) -> List[Task]:
        """Get all tasks for a specific user."""
        stmt = select(Task).where(Task.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, status_id: int) -> List[Task]:
        """Get all tasks with a specific status."""
        stmt = select(Task).where(Task.status_id == status_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_priority(self, priority_id: int) -> List[Task]:
        """Get all tasks with a specific priority."""
        stmt = select(Task).where(Task.priority_id == priority_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_external_sync_id(self, external_sync_id: str) -> Optional[Task]:
        """Get a task by its external sync ID."""
        stmt = select(Task).where(Task.external_sync_id == external_sync_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

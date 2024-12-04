from sqlalchemy.orm import Session
from sqlalchemy.future import select
from src.utils.datetime_utils import utc_now
from typing import List, Optional

from src.domain.models.task import Task
from src.application.schemas.task import TaskCreate, TaskUpdate

class TaskManager:
    def __init__(self, db: Session):
        self.db = db

    async def create_task(self, task: TaskCreate, user_id: int) -> Task:
        """Create a new task."""
        db_task = Task(
            user_id=user_id,
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            priority=task.priority,
            status=task.status or "pending"
        )
        self.db.add(db_task)
        await self.db.commit()
        await self.db.refresh(db_task)
        return db_task

    async def get_task(self, task_id: int, user_id: int) -> Optional[Task]:
        """Get a specific task by ID."""
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_tasks(self, user_id: int) -> List[Task]:
        """Get all tasks for a specific user."""
        stmt = select(Task).where(Task.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_task(self, task_id: int, task_update: TaskUpdate, user_id: int) -> Optional[Task]:
        """Update a task."""
        task = await self.get_task(task_id, user_id)
        if not task:
            return None

        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        task.updated_at = utc_now()

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: int, user_id: int) -> bool:
        """Delete a task."""
        task = await self.get_task(task_id, user_id)
        if not task:
            return False

        await self.db.delete(task)
        await self.db.commit()
        return True

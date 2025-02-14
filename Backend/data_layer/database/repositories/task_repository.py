from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from data_layer.database.models.task import Task


class TaskRepository:
    @staticmethod
    async def get_task_by_id(db: AsyncSession, task_id: int):
        """
        Retrieve a task by ID.
        """
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalars().first()

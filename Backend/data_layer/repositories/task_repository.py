from typing import Dict, List, Optional, cast, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from Backend.data_layer.database.models.task import Task, TaskStatus
from Backend.data_layer.database.models.task_history import TaskHistory
from datetime import datetime


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, **task_data) -> Task:
        """Create a new task."""
        task = Task(**task_data)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID."""
        result = await self.session.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_task_with_details(self, task_id: int) -> Optional[Task]:
        """Get a task with all its related details."""
        result = await self.session.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(
                joinedload(Task.attachments),
                joinedload(Task.comments),
                joinedload(Task.history),
                joinedload(Task.subtasks),
                joinedload(Task.workflow)
            )
        )
        return result.scalar_one_or_none()

    async def update_task(self, task_id: int, updates: Dict) -> Optional[Task]:
        """Update a task."""
        task = await self.get_task(task_id)
        if task:
            for key, value in updates.items():
                if value is not None:  # Only update non-None values
                    setattr(task, key, value)
            await self.session.commit()
            await self.session.refresh(task)
        return task

    async def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        task = await self.get_task(task_id)
        if task:
            await self.session.delete(task)
            await self.session.commit()
            return True
        return False

    async def get_tasks_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """Get tasks by project ID with optional filtering."""
        query = select(Task).where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == status)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_task_history(self, history: TaskHistory) -> TaskHistory:
        """Add a task history entry."""
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history

    async def get_task_metrics(self, task_id: int) -> Optional[Dict]:
        """Get task metrics and analytics."""
        task = await self.get_task(task_id)
        if not task:
            return None

        return {
            "time_tracking": {
                "time_spent": task.time_spent,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
            },
            "progress": {
                "status": task.status,
                "health_score": task.health_score,
                "complexity_score": task.complexity_score,
                "progress_metrics": task.progress_metrics,
            },
            "focus": {
                "focus_sessions": task.focus_sessions,
                "interruption_logs": task.interruption_logs,
            },
            "workflow": {
                "workflow_id": task.workflow_id,
                "current_step": task.current_workflow_step_id,
            }
        }

    async def get_task_history(
        self,
        task_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[TaskHistory]:
        """Get task history entries."""
        query = (
            select(TaskHistory)
            .where(TaskHistory.task_id == task_id)
            .order_by(TaskHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

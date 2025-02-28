from typing import Dict, List, Optional, cast, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from Backend.data_layer.database.models.task import Task, TaskStatus, TaskPriority
from Backend.data_layer.database.models.task_history import TaskHistory
from Backend.data_layer.database.models.task_agent_interaction import TaskAgentInteraction
from Backend.data_layer.database.models.ai_interactions import AIAgentInteraction
from datetime import datetime, timedelta
from Backend.data_layer.repositories.base_repository import BaseRepository
import logging
from Backend.data_layer.database.connection import get_db
import json
from sqlalchemy.future import select
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class TaskNotFoundError(Exception):
    """Raised when a task is not found."""
    pass


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db):
        self.db = db

    async def create(self, **task_data) -> Task:
        """Create a new task."""
        new_task = Task(**task_data)
        self.db.add(new_task)
        await self.db.flush()
        return new_task

    async def get_by_id(self, task_id: int, user_id: Optional[int] = None) -> Optional[Task]:
        """Get a task by ID with optional user ID check."""
        query = select(Task).where(Task.id == task_id)
        if user_id is not None:
            query = query.where(Task.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID."""
        return await self.get_by_id(task_id)

    async def update(self, task_id: int, user_id: int, **update_data) -> Optional[Task]:
        """Update a task."""
        task = await self.get_by_id(task_id, user_id)
        if task:
            for key, value in update_data.items():
                setattr(task, key, value)
            await self.db.flush()
            return task
        return None

    async def delete(self, task_id: int, user_id: int) -> bool:
        """Delete a task."""
        task = await self.get_by_id(task_id, user_id)
        if task:
            await self.db.delete(task)
            return True
        return False

    async def get_user_tasks(self, user_id: int, status: Optional[str] = None) -> List[Task]:
        """Get all tasks for a user with optional status filter."""
        query = select(Task).where(Task.user_id == user_id)
        if status:
            query = query.where(Task.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_task_with_details(self, task_id: int) -> Optional[Task]:
        """Get a task with all its related details."""
        query = (
            select(Task)
            .options(
                joinedload(Task.history),
                joinedload(Task.agent_interactions)
            )
            .where(Task.id == task_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update_task(self, task_id: int, task_data: dict) -> Optional[Task]:
        """Update a task with the given data."""
        task = await self.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")

        # Update task fields
        for key, value in task_data.items():
            if hasattr(task, key):
                setattr(task, key, value)

        await self.db.flush()
        return task

    async def get_tasks_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        due_date_start: Optional[datetime] = None,
        due_date_end: Optional[datetime] = None
    ) -> List[Task]:
        """Get tasks by project with optional filters."""
        query = select(Task).where(Task.project_id == project_id)
    
        # Apply filters
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assignee_id:
            query = query.where(Task.assignee_id == assignee_id)
        if creator_id:
            query = query.where(Task.creator_id == creator_id)
        if due_date_start:
            query = query.where(Task.due_date >= due_date_start)
        if due_date_end:
            query = query.where(Task.due_date <= due_date_end)
    
        # Apply pagination
        query = query.offset(skip).limit(limit)
    
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        due_date_start: Optional[datetime] = None,
        due_date_end: Optional[datetime] = None
    ) -> List[Task]:
        """Get all tasks with optional filters."""
        query = select(Task)
    
        # Apply filters
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assignee_id:
            query = query.where(Task.assignee_id == assignee_id)
        if creator_id:
            query = query.where(Task.creator_id == creator_id)
        if due_date_start:
            query = query.where(Task.due_date >= due_date_start)
        if due_date_end:
            query = query.where(Task.due_date <= due_date_end)
    
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_task_history(self, history: TaskHistory) -> TaskHistory:
        """Add a task history entry."""
        self.db.add(history)
        await self.db.flush()
        return history

    async def get_task_history(
        self,
        task_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[TaskHistory]:
        """Get paginated task history entries for a specific task."""
        query = (
            select(TaskHistory)
            .where(TaskHistory.task_id == task_id)
            .order_by(TaskHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent_tasks(
        self,
        user_id: int,
        days: int = 7,
        limit: int = 10
    ) -> List[Task]:
        """Get recent tasks for a user."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = (
            select(Task)
            .where(
                and_(
                    Task.user_id == user_id,
                    Task.created_at >= cutoff_date
                )
            )
            .order_by(Task.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_task_dependencies(self, task_id: int, dependencies: List[int]) -> bool:
        """Update task dependencies."""
        try:
            task = await self.get_task(task_id)
            if not task:
                return False

            task._dependencies_list = json.dumps(dependencies)
            await self.db.flush()
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating task dependencies: {str(e)}")
            return False

    async def track_ai_interaction(self, task_id: int, ai_result: Dict) -> None:
        """Track AI interaction for a task."""
        try:
            interaction = TaskAgentInteraction(
                task_id=task_id,
                agent_type=ai_result.get("agent_type", "unknown"),
                interaction_type=ai_result.get("interaction_type", "analysis"),
                result=ai_result.get("result"),
                success_rate=ai_result.get("confidence", 1.0)
            )
            self.db.add(interaction)
            await self.db.flush()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to track AI interaction: {str(e)}")
            raise

    async def create_task_agent_interaction(self, **interaction_data) -> TaskAgentInteraction:
        """Create a new task agent interaction."""
        interaction = TaskAgentInteraction(**interaction_data)
        self.db.add(interaction)
        await self.db.flush()
        return interaction

    async def get_task_agent_interactions(self, task_id: int) -> List[TaskAgentInteraction]:
        """Get all agent interactions for a task."""
        query = select(TaskAgentInteraction).where(
            TaskAgentInteraction.task_id == task_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_task_ai_metrics(self, task_id: int, metrics: Dict) -> Optional[Task]:
        """Update AI-related metrics for a task."""
        task = await self.get_task(task_id)
        if task:
            task.ai_suggestions = metrics.get(
                'suggestions', task.ai_suggestions)
            task.complexity_score = metrics.get(
                'complexity_score', task.complexity_score)
            task.health_score = metrics.get('health_score', task.health_score)
            task.risk_factors = metrics.get('risk_factors', task.risk_factors)
            await self.db.flush()
            return task
        return None

    async def track_ai_optimization(self, task_id: int, optimization_data: Dict) -> None:
        """Track AI optimization attempts for a task."""
        try:
            interaction = TaskAgentInteraction(
                task_id=task_id,
                agent_type="optimizer",
                interaction_type="optimization",
                result=optimization_data.get('result')
            )
            self.db.add(interaction)
            await self.db.flush()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error tracking AI optimization: {str(e)}")
            raise

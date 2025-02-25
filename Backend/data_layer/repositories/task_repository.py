from typing import Dict, List, Optional, cast, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from Backend.data_layer.database.models.task import Task, TaskStatus, TaskPriority
from Backend.data_layer.database.models.task_history import TaskHistory
from datetime import datetime
from Backend.data_layer.repositories.base_repository import BaseRepository
import logging
from Backend.data_layer.database.connection import get_db
import json

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository):
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
        result = await self.session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task:
            # Initialize dependencies from _dependencies_list
            try:
                deps = json.loads(task._dependencies_list) if task._dependencies_list else []
                task.dependencies = deps
                task.task_dependencies = deps  # Ensure both properties are set
            except (json.JSONDecodeError, TypeError):
                task.dependencies = []
                task.task_dependencies = []
        return task

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

    async def update_task(self, task_id: int, task_data: dict) -> Task:
        task = await self.session.get(Task, task_id)
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")

        for key, value in task_data.items():
            if hasattr(task, key):
                if key == 'dependencies':
                    # Store dependencies both as a list and JSON string
                    task.dependencies = value
                    task._dependencies_list = json.dumps(value)
                    task.task_dependencies = value  # Ensure task_dependencies is also set
                elif key == '_dependencies_list':
                    # Ensure _dependencies_list is always a JSON string
                    task._dependencies_list = value if isinstance(value, str) else json.dumps(value)
                    task.dependencies = json.loads(value if isinstance(value, str) else json.dumps(value))
                    task.task_dependencies = task.dependencies  # Keep task_dependencies in sync
                else:
                    setattr(task, key, value)

        await self.session.commit()
        await self.session.refresh(task)
        # Ensure dependencies are properly set after refresh
        if task._dependencies_list:
            deps = json.loads(task._dependencies_list)
            task.dependencies = deps
            task.task_dependencies = deps
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
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        due_date_start: Optional[datetime] = None,
        due_date_end: Optional[datetime] = None
    ) -> List[Task]:
        """Get tasks by project ID with optional filtering."""
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
        
        # Execute query
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

    async def get_due_todos(self):
        return await self.get_due_todos()

    async def get_recurring_todos(self):
        return await self.get_recurring_todos()

    async def create_recurring_instance(self, original_todo, next_date):
        return await self.create_recurring_instance(original_todo, next_date)

    async def update_next_occurrence(self, todo_id: int, next_occurrence: datetime):
        return await self.update_next_occurrence(todo_id, next_occurrence)

    async def update_task_dependencies(self, task_id: int, dependencies: List[int]) -> bool:
        """Update task dependencies."""
        try:
            task = await self.session.get(Task, task_id)
            if not task:
                return False

            # Validate that all dependency tasks exist
            for dep_id in dependencies:
                dep_task = await self.get_task(dep_id)
                if not dep_task:
                    raise ValueError(f"Dependency task {dep_id} not found")

            # Update dependencies - store both as list and JSON string
            task.dependencies = dependencies
            task._dependencies_list = json.dumps(dependencies)
            task.task_dependencies = dependencies  # Ensure task_dependencies is also set
            await self.session.commit()
            await self.session.refresh(task)
            # Ensure dependencies are properly set after refresh
            task.dependencies = dependencies
            task.task_dependencies = dependencies
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating task dependencies: {str(e)}")
            return False

# Add to TaskRepository class
async def track_ai_interaction(self, task_id: int, ai_result: Dict) -> None:
    """Track AI interaction for a task."""
    try:
        interaction = AIAgentInteraction(
            task_id=task_id,
            ai_model_id=ai_result.get("model_id"),
            interaction_type="task_classification",
            input_data=ai_result.get("input"),
            output_data=ai_result.get("output"),
            success_rate=ai_result.get("confidence", 1.0)
        )
        self.session.add(interaction)
        await self.session.commit()
    except Exception as e:
        logger.error(f"Error tracking AI interaction: {str(e)}")
        await self.session.rollback()
        logger.error(f"Failed to track AI interaction: {str(e)}")
        raise


async def create_task_agent_interaction(self, **interaction_data) -> TaskAgentInteraction:
    """Create a new task agent interaction."""
    interaction = TaskAgentInteraction(**interaction_data)
    self.session.add(interaction)
    await self.session.commit()
    await self.session.refresh(interaction)
    return interaction

async def get_task_agent_interactions(self, task_id: int) -> List[TaskAgentInteraction]:
    """Get all agent interactions for a task."""
    query = select(TaskAgentInteraction).where(TaskAgentInteraction.task_id == task_id)
    result = await self.session.execute(query)
    return list(result.scalars().all())

async def update_task_ai_metrics(self, task_id: int, metrics: Dict) -> Task:
    """Update AI-related metrics for a task."""
    task = await self.get_task(task_id)
    if task:
        task.ai_suggestions = metrics.get('suggestions', task.ai_suggestions)
        task.complexity_score = metrics.get('complexity_score', task.complexity_score)
        task.health_score = metrics.get('health_score', task.health_score)
        task.risk_factors = metrics.get('risk_factors', task.risk_factors)
        await self.session.commit()
        await self.session.refresh(task)
    return task

async def track_ai_optimization(self, task_id: int, optimization_data: Dict) -> None:
    """Track AI optimization attempts for a task."""
    try:
        task = await self.get_task(task_id)
        if task:
            interaction = TaskAgentInteraction(
                task_id=task_id,
                interaction_type="optimization",
                confidence_score=optimization_data.get('confidence_score'),
                recommendations=optimization_data.get('recommendations'),
                result=optimization_data.get('result')
            )
            self.session.add(interaction)
            await self.session.commit()
    except Exception as e:
        logger.error(f"Error tracking AI optimization: {str(e)}")
        await self.session.rollback()

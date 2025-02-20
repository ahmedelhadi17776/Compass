from typing import List, Dict, Optional
from datetime import datetime
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.database.models.task import Task, TaskStatus, TaskPriority
from Backend.data_layer.database.models.task_history import TaskHistory
from Backend.data_layer.database.errors import TaskNotFoundError
from Backend.tasks.task_tasks import process_task, execute_task_step
from celery.result import AsyncResult
import asyncio


class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    async def create_task(
        self,
        title: str,
        description: Optional[str],
        creator_id: int,
        project_id: int,
        organization_id: int,
        workflow_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        reviewer_id: Optional[int] = None,
        priority: Optional[TaskPriority] = TaskPriority.MEDIUM,
        category_id: Optional[int] = None,
        parent_task_id: Optional[int] = None,
        estimated_hours: Optional[float] = None,
        due_date: Optional[datetime] = None
    ) -> Dict:
        task = await self.repository.create_task(
            title=title,
            description=description,
            status=TaskStatus.TODO,
            creator_id=creator_id,
            project_id=project_id,
            organization_id=organization_id,
            workflow_id=workflow_id,
            assignee_id=assignee_id,
            reviewer_id=reviewer_id,
            priority=priority,
            category_id=category_id,
            parent_task_id=parent_task_id,
            estimated_hours=estimated_hours,
            due_date=due_date,
            health_score=1.0  # Initial perfect health score
        )

        # If the task is part of a workflow, trigger workflow step execution
        if workflow_id:
            workflow_step_id = task.workflow.steps[0].id if task.workflow.steps else None
            if workflow_step_id:
                await execute_task_step.delay(
                    task_id=task.id,
                    workflow_step_id=workflow_step_id,
                    user_id=creator_id
                )

        return {
            "task_id": task.id,
            "status": task.status,
            "workflow_id": workflow_id,
            "current_workflow_step_id": workflow_step_id if workflow_id else None
        }

    async def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        assignee_id: Optional[int] = None,
        reviewer_id: Optional[int] = None,
        priority: Optional[TaskPriority] = None,
        category_id: Optional[int] = None,
        due_date: Optional[datetime] = None,
        actual_hours: Optional[float] = None,
        progress_metrics: Optional[Dict] = None,
        blockers: Optional[Dict] = None,
        user_id: int
    ) -> Dict:
        task = await self.repository.get_task(task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        # Calculate health score based on various factors
        health_score = await self._calculate_health_score(
            task,
            status,
            due_date,
            blockers
        )

        # Update task fields
        updates = {
            "title": title,
            "description": description,
            "status": status,
            "assignee_id": assignee_id,
            "reviewer_id": reviewer_id,
            "priority": priority,
            "category_id": category_id,
            "due_date": due_date,
            "actual_hours": actual_hours,
            "progress_metrics": progress_metrics,
            "blockers": blockers,
            "health_score": health_score
        }

        # If task is completed, set completed_at
        if status == TaskStatus.COMPLETED and task.status != TaskStatus.COMPLETED:
            updates["completed_at"] = datetime.utcnow()

        await self.repository.update_task(task_id, updates)

        # Record task history
        history = TaskHistory(
            task_id=task_id,
            user_id=user_id,
            action="update",
            field="multiple",
            new_value=str(updates)
        )
        await self.repository.add_task_history(history)

        return {
            "task_id": task_id,
            "status": status or task.status,
            "health_score": health_score
        }

    async def _calculate_health_score(
        self,
        task: Task,
        new_status: Optional[TaskStatus],
        new_due_date: Optional[datetime],
        blockers: Optional[Dict]
    ) -> float:
        """Calculate task health score based on various factors."""
        score = 1.0  # Start with perfect health

        # Status impact
        if new_status == TaskStatus.BLOCKED:
            score *= 0.5
        elif new_status == TaskStatus.DEFERRED:
            score *= 0.7

        # Due date impact
        if new_due_date and new_due_date < datetime.utcnow():
            score *= 0.8

        # Blockers impact
        if blockers and len(blockers) > 0:
            score *= 0.9

        # Bound score between 0 and 1
        return max(0.0, min(1.0, score))

    async def get_task_with_details(self, task_id: int) -> Dict:
        """Get task with all related details."""
        task = await self.repository.get_task_with_details(task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")
        return task

    async def get_task_metrics(self, task_id: int) -> Dict:
        """Get task metrics including time tracking and progress."""
        task = await self.repository.get_task(task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        return {
            "time_spent": task.time_spent,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "health_score": task.health_score,
            "complexity_score": task.complexity_score,
            "progress_metrics": task.progress_metrics,
            "focus_sessions": task.focus_sessions,
            "interruption_logs": task.interruption_logs
        }

    async def execute_task_step(
        self,
        task_id: int,
        workflow_step_id: int,
        user_id: int
    ) -> Dict:
        task = await self.repository.get_task(task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        # Start step execution in background
        task = execute_task_step.delay(
            task_id=task_id,
            workflow_step_id=workflow_step_id,
            user_id=user_id
        )

        return {
            "task_id": task_id,
            "step_id": workflow_step_id,
            "task_id": task.id,
            "status": "PENDING"
        }

    async def get_task_status(self, task_id: str) -> Dict:
        result = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None
        }

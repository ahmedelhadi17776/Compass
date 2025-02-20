from Backend.core.celery_app import celery_app
from Backend.data_layer.database.models.task import TaskStatus
from Backend.data_layer.database.models.workflow import WorkflowStatus
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.data_layer.database.connection import async_session
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
import logging
import asyncio
from typing import Dict, Any, cast
from sqlalchemy.sql.elements import ColumnElement

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.task_tasks.process_task",
    queue="tasks",
    priority=5,
    retry_backoff=True,
    max_retries=3
)
def process_task(task_id: int, user_id: int):
    """Process a task asynchronously with proper error handling and status updates."""
    async def _process():
        async with async_session() as session:
            task_repo = TaskRepository(session)

            # Get task and update status
            task = await task_repo.get_task(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            # Update task status to in progress
            updates = {
                "status": TaskStatus.IN_PROGRESS,
                "time_spent": 0,
                "progress_metrics": {"started_at": datetime.utcnow().isoformat()}
            }
            await task_repo.update_task(task_id, updates)

            # Process task based on its configuration
            result = {
                "task_id": task_id,
                "status": "processed",
                "processed_at": datetime.utcnow().isoformat(),
                "processor_id": user_id
            }

            # Update task with completion data
            task_metrics = {}
            if isinstance(task.progress_metrics, dict):
                task_metrics = task.progress_metrics
            task_metrics.update({
                "completed_at": datetime.utcnow().isoformat(),
                "processing_result": result
            })

            completion_updates = {
                "status": TaskStatus.COMPLETED,
                "completed_at": datetime.utcnow(),
                "progress_metrics": task_metrics
            }
            await task_repo.update_task(task_id, completion_updates)
            await session.commit()

            return result

    try:
        return asyncio.run(_process())
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {str(e)}")

        async def _handle_error():
            async with async_session() as session:
                task_repo = TaskRepository(session)
                await task_repo.update_task(task_id, {
                    "status": TaskStatus.BLOCKED,
                    "blockers": {
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                await session.commit()

        try:
            asyncio.run(_handle_error())
        except:
            pass
        raise


@celery_app.task(
    name="tasks.task_tasks.execute_task_step",
    queue="tasks",
    priority=6,
    retry_backoff=True,
    max_retries=3
)
def execute_task_step(task_id: int, workflow_step_id: int, user_id: int):
    """Execute a workflow step for a task with proper tracking and error handling."""
    async def _execute():
        async with async_session() as session:
            task_repo = TaskRepository(session)
            workflow_repo = WorkflowRepository(session)

            # Get task and workflow step
            task = await task_repo.get_task(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            step = await workflow_repo.get_workflow_step(workflow_step_id)
            if not step:
                raise ValueError(f"Workflow step {workflow_step_id} not found")

            # Update task with current step
            await task_repo.update_task(task_id, {
                "current_workflow_step_id": workflow_step_id,
                "status": TaskStatus.IN_PROGRESS,
                "progress_metrics": {
                    "current_step": {
                        "id": workflow_step_id,
                        "name": step.name,
                        "started_at": datetime.utcnow().isoformat()
                    }
                }
            })

            # Execute step based on its configuration
            step_result = {
                "step_id": workflow_step_id,
                "status": "completed",
                "executed_at": datetime.utcnow().isoformat(),
                "executor_id": user_id
            }

            # Update task with step completion
            task_metrics = {}
            if isinstance(task.progress_metrics, dict):
                task_metrics = task.progress_metrics
            task_metrics.update({
                "current_step": {
                    "id": workflow_step_id,
                    "name": step.name,
                    "completed_at": datetime.utcnow().isoformat(),
                    "result": step_result
                }
            })

            await task_repo.update_task(task_id, {
                "progress_metrics": task_metrics
            })
            await session.commit()

            return {
                "task_id": task_id,
                "step_id": workflow_step_id,
                "status": "completed",
                "result": step_result
            }

    try:
        return asyncio.run(_execute())
    except Exception as e:
        logger.error(
            f"Error executing step {workflow_step_id} for task {task_id}: {str(e)}")

        async def _handle_error():
            async with async_session() as session:
                task_repo = TaskRepository(session)
                await task_repo.update_task(task_id, {
                    "status": TaskStatus.BLOCKED,
                    "blockers": {
                        "error": str(e),
                        "step_id": workflow_step_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                await session.commit()

        try:
            asyncio.run(_handle_error())
        except:
            pass
        raise

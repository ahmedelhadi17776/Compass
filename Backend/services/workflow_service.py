from typing import List, Dict, Optional
from datetime import datetime
from Backend.tasks.workflow_tasks import process_workflow, execute_workflow_step
from Backend.tasks.notification_tasks import send_notification
from Backend.tasks.ai_tasks import process_text_analysis, generate_productivity_insights
from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
from Backend.core.celery_app import celery_app
from Backend.data_layer.database.models.workflow import Workflow, WorkflowStatus
from celery.result import AsyncResult
from Backend.data_layer.database.errors import WorkflowNotFoundError
import asyncio


class WorkflowService:
    def __init__(self, repository: WorkflowRepository):
        self.repository = repository

    async def create_workflow(
        self,
        user_id: int,
        organization_id: int,
        name: str,
        description: str,
        steps: List[Dict]
    ) -> Dict:
        # Create workflow with pending status
        workflow = await self.repository.create_workflow(
            user_id=user_id,
            organization_id=organization_id,
            name=name,
            description=description,
            status=WorkflowStatus.PENDING.value
        )

        # Start workflow processing in background
        task = process_workflow.delay(
            workflow_id=workflow.id,
            steps=steps,
            user_id=user_id
        )

        # Wait briefly to ensure task is registered
        await asyncio.sleep(0.5)

        return {
            "workflow_id": workflow.id,
            "task_id": task.id,
            "status": workflow.status
        }

    async def execute_step(
        self,
        workflow_id: int,
        step_id: int,
        user_id: int,
        input_data: Dict
    ) -> Dict:
        # Get workflow with steps
        workflow = await self.repository.get_workflow(workflow_id, with_steps=True)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        # Verify workflow status
        if workflow.status not in [WorkflowStatus.PENDING.value, WorkflowStatus.ACTIVE.value]:
            raise ValueError(
                f"Workflow is in {workflow.status} state and cannot execute steps")

        # Start step execution in background
        task = execute_workflow_step.delay(
            workflow_id=workflow_id,
            step_id=step_id,
            input_data=input_data,
            user_id=user_id
        )

        # Wait briefly to ensure task is registered
        await asyncio.sleep(0.5)

        return {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "task_id": task.id,
            "status": "PENDING"
        }

    async def analyze_workflow(
        self,
        workflow_id: int,
        user_id: int,
        analysis_type: str,
        time_range: str,
        metrics: List[str]
    ) -> Dict:
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        # Start analysis in background
        task = process_text_analysis.delay(
            workflow_id=workflow_id,
            analysis_type=analysis_type,
            time_range=time_range,
            metrics=metrics,
            user_id=user_id
        )

        # Wait briefly to ensure task is registered
        await asyncio.sleep(0.5)

        return {
            "workflow_id": workflow_id,
            "analysis_task_id": task.id,
            "status": "PENDING"
        }

    async def get_task_status(self, task_id: str) -> Dict:
        result = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None
        }

    async def cancel_workflow(
        self,
        workflow_id: int,
        user_id: int
    ) -> Dict:
        # Get workflow and verify ownership
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        if workflow.created_by != user_id:
            raise ValueError("User is not authorized to cancel this workflow")

        # Update workflow status to cancelled
        success = await self.repository.update_workflow_status(
            workflow_id=workflow_id,
            status=WorkflowStatus.CANCELLED.value
        )

        if not success:
            raise ValueError(f"Failed to cancel workflow {workflow_id}")

        return {
            "workflow_id": workflow_id,
            "status": WorkflowStatus.CANCELLED.value,
            "task_id": None  # No task ID since this is a direct status update
        }

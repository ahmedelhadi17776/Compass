from typing import List, Dict, Optional
from datetime import datetime
from Backend.celery_app.tasks.workflow_tasks import process_workflow, execute_workflow_step
from Backend.celery_app.tasks.notification_tasks import send_notification
from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
from Backend.celery_app.tasks.workflow_tasks import (
    create_workflow_task,
    update_workflow_task,
    delete_workflow_task,
    get_workflows_task,
    get_workflow_by_id_task
)
from Backend.services.ai_service import AIService
from Backend.data_layer.database.models.workflow import Workflow, WorkflowStatus, WorkflowType
from Backend.data_layer.database.models.workflow_step import WorkflowStep
from Backend.data_layer.database.models.workflow_execution import WorkflowExecution
from celery.result import AsyncResult
from Backend.data_layer.database.errors import WorkflowNotFoundError
import asyncio
from sqlalchemy import inspect, and_, or_



class WorkflowService:
    def __init__(self, repository: WorkflowRepository):
        self.repository = repository

    async def create_workflow(
        self,
        name: str,
        description: str,
        creator_id: int,
        organization_id: int,
        workflow_type: WorkflowType = WorkflowType.SEQUENTIAL,
        config: Optional[Dict] = None,
        steps: Optional[List[Dict]] = None,
        ai_enabled: bool = False,
        ai_confidence_threshold: Optional[float] = None,
        estimated_duration: Optional[int] = None,
        deadline: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """Create a new workflow with steps."""
        workflow_data = {
            "name": name,
            "description": description,
            "workflow_type": workflow_type,
            "created_by": creator_id,
            "organization_id": organization_id,
            "config": config or {},
            "status": WorkflowStatus.PENDING,
            "ai_enabled": ai_enabled,
            "ai_confidence_threshold": ai_confidence_threshold,
            "estimated_duration": estimated_duration,
            "deadline": deadline,
            "tags": tags or [],
            "workflow_metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0",
                "creator_id": creator_id
            }
        }

        # Create workflow using Celery task
        workflow = await create_workflow_task.delay(workflow_data=workflow_data)

        if steps:
            for step_data in steps:
                await self.repository.create_workflow_step(
                    workflow_id=workflow.id,
                    **step_data
                )

        return {
            "workflow_id": workflow.id,
            "status": workflow.status,
            "type": workflow.workflow_type,
            "steps_count": len(steps) if steps else 0
        }

    async def execute_step(
        self,
        workflow_id: int,
        step_id: int,
        user_id: int,
        input_data: Optional[Dict] = None
    ) -> Dict:
        """Execute a specific workflow step."""
        workflow = await get_workflow_by_id_task.delay(workflow_id=workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        step = await self.repository.get_workflow_step(step_id)
        if not step:
            raise ValueError(f"Step {step_id} not found")

        # Update workflow status to active
        await update_workflow_task.delay(
            workflow_id=workflow_id,
            updates={"status": WorkflowStatus.ACTIVE.value}
        )

        # Create execution record
        execution = await self.repository.create_workflow_execution(
            workflow_id=workflow_id,
            status=WorkflowStatus.ACTIVE
        )

        # Create step execution record
        step_execution = await self.repository.create_step_execution(
            execution_id=execution.__dict__['id'],
            step_id=step_id,
            status="pending"
        )

        # Execute step in background
        task = execute_workflow_step.delay(
            workflow_id=workflow_id,
            step_id=step_id,
            execution_id=execution.__dict__['id'],
            user_id=user_id,
            input_data=input_data or {}
        )

        return {
            "execution_id": execution.__dict__['id'],
            "step_execution_id": step_execution.id,
            "task_id": task.id,
            "status": "pending"
        }

    async def analyze_workflow(
        self,
        workflow_id: int,
        user_id: int,
        analysis_type: str,
        time_range: str,
        metrics: List[str]
    ) -> Dict:
        """Analyze workflow using AI service."""
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow with id {workflow_id} not found")

        # Delegate analysis to AI service
        ai_service = AIService()
        return await ai_service.analyze_workflow(
            workflow_id=workflow_id,
            user_id=user_id,
            analysis_type=analysis_type,
            time_range=time_range,
            metrics=metrics
        )

    async def update_workflow(
        self,
        workflow_id: int,
        updates: Dict,
        user_id: int
    ) -> Dict:
        """Update workflow configuration and metadata."""
        workflow = await update_workflow_task.delay(workflow_id=workflow_id, updates=updates)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        return {
            "workflow_id": workflow_id,
            "status": workflow.status,
            "updated_at": workflow.updated_at.isoformat()
        }

    async def cancel_workflow(
        self,
        workflow_id: int,
        user_id: int
    ) -> Dict:
        """Cancel a workflow and all its pending executions."""
        workflow = await get_workflow_by_id_task.delay(workflow_id=workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        # Update workflow status
        await update_workflow_task.delay(
            workflow_id=workflow_id,
            updates={"status": WorkflowStatus.CANCELLED}
        )

        # Cancel any active executions
        await self.repository.cancel_active_executions(workflow_id)

        return {
            "workflow_id": workflow_id,
            "status": WorkflowStatus.CANCELLED,
            "cancelled_at": datetime.utcnow().isoformat()
        }

    async def get_workflow_metrics(
        self,
        workflow_id: int
    ) -> Dict:
        """Get comprehensive workflow metrics and analytics."""
        workflow = await self.repository.get_workflow_with_metrics(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        # Calculate efficiency ratio safely
        efficiency_ratio = None
        estimated_duration = getattr(workflow, 'estimated_duration', None)
        actual_duration = getattr(workflow, 'actual_duration', None)
        if estimated_duration is not None and actual_duration is not None and estimated_duration != 0:
            try:
                efficiency_ratio = actual_duration / estimated_duration
            except (TypeError, ZeroDivisionError):
                efficiency_ratio = None

        return {
            "performance": {
                "average_completion_time": workflow.average_completion_time,
                "success_rate": workflow.success_rate,
                "optimization_score": workflow.optimization_score
            },
            "execution": {
                "total_executions": len(workflow.executions),
                "successful_executions": sum(1 for e in workflow.executions if e.status == WorkflowStatus.COMPLETED),
                "failed_executions": sum(1 for e in workflow.executions if e.status == WorkflowStatus.FAILED)
            },
            "timing": {
                "estimated_duration": estimated_duration,
                "actual_duration": actual_duration,
                "efficiency_ratio": efficiency_ratio
            },
            "ai_metrics": {
                "ai_enabled": workflow.ai_enabled,
                "confidence_threshold": workflow.ai_confidence_threshold,
                "learning_progress": workflow.ai_learning_data.get("learning_progress") if getattr(workflow, 'ai_learning_data', None) is not None else None
            }
        }

    async def get_task_status(self, task_id: str) -> Dict:
        """Get the status of a Celery task."""
        result = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None
        }

    # Add error handling for AI service failures


    async def optimize_workflow(self, workflow_id: int) -> Dict:
        """Optimize workflow using AI service."""
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        # Delegate optimization to AI service
        ai_service = AIService()
        optimization_result = await ai_service.optimize_workflow(workflow_id)

        # Update workflow with optimization results
        await self.update_workflow(
            workflow_id=workflow_id,
            updates={
                "optimization_score": optimization_result.get("optimization_score"),
                "ai_recommendations": optimization_result.get("recommendations", []),
                "last_optimized": datetime.utcnow().isoformat()
            },
            user_id=workflow.created_by
        )

        return optimization_result
        
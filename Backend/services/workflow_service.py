from typing import List, Dict, Optional
from datetime import datetime
from Backend.tasks.workflow_tasks import process_workflow, execute_workflow_step
from Backend.tasks.notification_tasks import send_notification
from Backend.tasks.ai_tasks import process_text_analysis, generate_productivity_insights
from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
from Backend.core.celery_app import celery_app
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
        workflow = await self.repository.create_workflow(
            name=name,
            description=description,
            workflow_type=workflow_type,
            created_by=creator_id,
            organization_id=organization_id,
            config=config or {},
            status=WorkflowStatus.PENDING,
            ai_enabled=ai_enabled,
            ai_confidence_threshold=ai_confidence_threshold,
            estimated_duration=estimated_duration,
            deadline=deadline,
            tags=tags or [],
            workflow_metadata={
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0",
                "creator_id": creator_id
            }
        )

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
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        step = await self.repository.get_workflow_step(step_id)
        if not step:
            raise ValueError(f"Step {step_id} not found")

        # Update workflow status to active
        await self.repository.update_workflow_status(workflow_id, WorkflowStatus.ACTIVE.value)

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
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow with id {workflow_id} not found")

        # Get workflow metrics safely
        estimated_duration = getattr(workflow, 'estimated_duration', None)
        actual_duration = getattr(workflow, 'actual_duration', None)
        ai_enabled = bool(getattr(workflow, 'ai_enabled', False))
        ai_confidence = getattr(workflow, 'ai_confidence_threshold', None)
        ai_learning_data = getattr(workflow, 'ai_learning_data', {})
        learning_progress = ai_learning_data.get(
            "learning_progress") if ai_learning_data else None

        efficiency_ratio = None
        if estimated_duration is not None and actual_duration is not None and estimated_duration > 0:
            efficiency_ratio = actual_duration / estimated_duration

        # Get executions count
        executions = await self.repository.get_workflow_executions(workflow_id)
        total_executions = len(executions)
        successful_executions = sum(1 for e in executions if str(
            e.status) == WorkflowStatus.COMPLETED.value)
        failed_executions = sum(1 for e in executions if str(
            e.status) == WorkflowStatus.FAILED.value)

        # Calculate metrics based on requested analysis
        metrics_data = {
            "performance": {
                "average_completion_time": getattr(workflow, 'average_completion_time', None),
                "success_rate": getattr(workflow, 'success_rate', None),
                "optimization_score": getattr(workflow, 'optimization_score', None)
            },
            "execution": {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions
            },
            "timing": {
                "estimated_duration": estimated_duration,
                "actual_duration": actual_duration,
                "efficiency_ratio": efficiency_ratio
            },
            "ai_metrics": {
                "ai_enabled": ai_enabled,
                "confidence_threshold": ai_confidence,
                "learning_progress": learning_progress
            }
        }

        # Prepare analysis data
        analysis_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": analysis_type,
            "time_range": time_range,
            "metrics": metrics_data
        }

        # Get current metadata and update it
        current_metadata = workflow.workflow_metadata if workflow.workflow_metadata is not None else {}
        if isinstance(current_metadata, dict):
            current_metadata = current_metadata.copy()
        else:
            current_metadata = {}
        current_metadata["analysis"] = analysis_data

        # Update workflow metadata in database
        await self.repository.update_workflow(workflow_id, {
            "workflow_metadata": current_metadata
        })

        return metrics_data

    async def update_workflow(
        self,
        workflow_id: int,
        updates: Dict,
        user_id: int
    ) -> Dict:
        """Update workflow configuration and metadata."""
        workflow = await self.repository.update_workflow(workflow_id, updates)
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
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        # Update workflow status
        await self.repository.update_workflow(
            workflow_id,
            {"status": WorkflowStatus.CANCELLED}
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
        result = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None
        }

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

        # Create workflow directly using the repository instead of Celery task
        workflow = await self.repository.create_workflow(**workflow_data)
        
        if steps:
            for i, step_data in enumerate(steps):
                # Ensure step_order is set if not provided
                if 'step_order' not in step_data:
                    step_data['step_order'] = i + 1
                
                # Ensure step has workflow_id
                step_data['workflow_id'] = workflow.id
                
                await self.repository.create_workflow_step(**step_data)

        return {
            "workflow_id": workflow.id,
            "status": workflow.status.value,  # Use .value for enum
            "type": workflow.workflow_type.value,  # Use .value for enum
            "steps_count": len(steps) if steps else 0
        }

    async def execute_step(
        self,
        workflow_id: int,
        step_id: int,
        user_id: int,
        input_data: Optional[Dict] = None,
        transition_id: Optional[int] = None
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

        # Validate transition if provided
        if transition_id:
            transitions = await self.repository.get_workflow_transitions(workflow_id)
            valid_transition = any(
                t.id == transition_id and t.to_step_id == step_id for t in transitions)
            if not valid_transition:
                raise ValueError(
                    f"Invalid transition {transition_id} for step {step_id}")

        # Create step execution record with metadata
        execution_metadata = {
            "user_id": user_id,
            "transition_id": transition_id,
            "input_validation": True
        }

        step_execution = await self.repository.create_step_execution(
            execution_id=execution.__dict__['id'],
            step_id=step_id,
            status="pending",
            execution_metadata=execution_metadata
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
        # Start a Celery task to update the workflow
        task = update_workflow_task.delay(workflow_id=workflow_id, updates=updates)
        
        try:
            # Wait for the result with a timeout
            workflow_result = task.get(timeout=10)  # Wait up to 10 seconds
            
            return {
                "workflow_id": workflow_id,
                "status": workflow_result["status"],
                "task_id": task.id
            }
        except Exception as e:
            # Return the task ID for later checking if timeout or error
            return {
                "workflow_id": workflow_id,
                "task_id": task.id,
                "status": "pending"
            }
        # Remove unreachable code
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

    async def get_workflow_with_details(self, workflow_id: int) -> Optional[Dict]:
        """Get a workflow with all its details and related data."""
        workflow = await self.repository.get_workflow_with_metrics(workflow_id)
        
        if not workflow:
            return None
            
        # Convert workflow to dictionary with all related data
        result = {
            "id": workflow.id,  # Use id instead of workflow_id
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status.value if hasattr(workflow.status, 'value') else workflow.status,
            "workflow_type": workflow.workflow_type.value if hasattr(workflow.workflow_type, 'value') else workflow.workflow_type,
            "created_by": workflow.created_by,
            "organization_id": workflow.organization_id,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
            "config": workflow.config,
            "ai_enabled": workflow.ai_enabled,
            "ai_confidence_threshold": workflow.ai_confidence_threshold,
            "estimated_duration": workflow.estimated_duration,
            "deadline": workflow.deadline.isoformat() if workflow.deadline else None,
            "tags": workflow.tags,
            "workflow_metadata": workflow.workflow_metadata,
            "version": workflow.version or "1.0.0",  # Add version field
            "optimization_score": workflow.optimization_score or 0.0,  # Add optimization_score field
            "steps": [],  # Initialize empty steps array
            "tasks": [],  # Initialize empty tasks array
            "executions": []  # Initialize empty executions array
        }
        
        # Add steps if available
        if hasattr(workflow, 'steps') and workflow.steps:
            result["steps"] = [
                {
                    "id": step.id,
                    "name": step.name,
                    "description": step.description,
                    "step_type": step.step_type.value if hasattr(step.step_type, 'value') else step.step_type,
                    "step_order": step.step_order,
                    "status": step.status.value if hasattr(step.status, 'value') else step.status,
                    "config": step.config,
                    "timeout": step.timeout,
                    "is_required": step.is_required,
                    "auto_advance": step.auto_advance,
                    "can_revert": step.can_revert,
                    "dependencies": step.dependencies,
                    "version": step.version,
                    "assigned_to": step.assigned_to,
                    "average_execution_time": step.average_execution_time,
                    "success_rate": step.success_rate
                }
                for step in workflow.steps
            ]
        
        # Add executions if available
        if hasattr(workflow, 'executions') and workflow.executions:
            result["executions"] = [
                {
                    "id": execution.id,
                    "status": execution.status.value if hasattr(execution.status, 'value') else execution.status,
                    "started_at": execution.started_at.isoformat() if execution.started_at else None,
                    "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                    "execution_time": execution.execution_time,
                    "result": execution.result,
                    "error": execution.error
                }
                for execution in workflow.executions
            ]
            
        # Add agent links if available
        if hasattr(workflow, 'agent_links') and workflow.agent_links:
            result["agent_links"] = [
                {
                    "id": link.id,
                    "agent_id": link.agent_id,
                    "role": link.role,
                    "permissions": link.permissions
                }
                for link in workflow.agent_links
            ]
            
        return result

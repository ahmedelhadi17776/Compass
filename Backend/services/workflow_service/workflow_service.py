"""Workflow service module."""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ...data.repositories.workflow_repository import WorkflowRepository
from ...data.database.models.workflow import Workflow
from core.exceptions import WorkflowNotFoundError

class WorkflowService:
    """Workflow service class."""

    def __init__(self, session: AsyncSession):
        """Initialize workflow service."""
        self._repository = WorkflowRepository(session)

    async def create_workflow(
        self,
        user_id: int,
        name: str,
        steps: List[Dict],
        description: Optional[str] = None,
        triggers: Optional[List[Dict]] = None
    ) -> Workflow:
        """Create a new workflow."""
        # Validate workflow steps
        self._validate_workflow_steps(steps)

        # Validate triggers if provided
        if triggers:
            self._validate_workflow_triggers(triggers)

        return await self._repository.create_workflow({
            "user_id": user_id,
            "name": name,
            "description": description,
            "steps": steps,
            "triggers": triggers,
            "status": "draft",
            "is_active": False
        })

    def _validate_workflow_steps(self, steps: List[Dict]) -> None:
        """Validate workflow steps."""
        if not steps:
            raise ValueError("Workflow must have at least one step")

        required_fields = ["type", "action"]
        valid_step_types = ["task", "notification", "device_control", "web_search", "ai_action"]

        for step in steps:
            # Check required fields
            for field in required_fields:
                if field not in step:
                    raise ValueError(f"Step missing required field: {field}")

            # Validate step type
            if step["type"] not in valid_step_types:
                raise ValueError(f"Invalid step type. Must be one of: {valid_step_types}")

    def _validate_workflow_triggers(self, triggers: List[Dict]) -> None:
        """Validate workflow triggers."""
        valid_trigger_types = ["schedule", "event", "condition"]
        required_fields = ["type", "configuration"]

        for trigger in triggers:
            # Check required fields
            for field in required_fields:
                if field not in trigger:
                    raise ValueError(f"Trigger missing required field: {field}")

            # Validate trigger type
            if trigger["type"] not in valid_trigger_types:
                raise ValueError(f"Invalid trigger type. Must be one of: {valid_trigger_types}")

    async def get_workflow(self, workflow_id: int) -> Workflow:
        """Get a specific workflow."""
        return await self._repository.get_workflow(workflow_id)

    async def get_user_workflows(
        self,
        user_id: int,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Workflow]:
        """Get workflows for a user."""
        return await self._repository.get_user_workflows(
            user_id,
            status,
            is_active
        )

    async def update_workflow(
        self,
        workflow_id: int,
        workflow_data: Dict
    ) -> Workflow:
        """Update workflow details."""
        # Validate steps if provided
        if "steps" in workflow_data:
            self._validate_workflow_steps(workflow_data["steps"])

        # Validate triggers if provided
        if "triggers" in workflow_data:
            self._validate_workflow_triggers(workflow_data["triggers"])

        return await self._repository.update_workflow(
            workflow_id,
            workflow_data
        )

    async def activate_workflow(
        self,
        workflow_id: int
    ) -> Workflow:
        """Activate a workflow."""
        workflow = await self.get_workflow(workflow_id)
        
        # Validate workflow before activation
        self._validate_workflow_steps(workflow.steps)
        if workflow.triggers:
            self._validate_workflow_triggers(workflow.triggers)

        return await self._repository.update_workflow(
            workflow_id,
            {
                "status": "active",
                "is_active": True,
                "activated_at": datetime.utcnow()
            }
        )

    async def deactivate_workflow(
        self,
        workflow_id: int
    ) -> Workflow:
        """Deactivate a workflow."""
        return await self._repository.update_workflow(
            workflow_id,
            {
                "status": "inactive",
                "is_active": False,
                "deactivated_at": datetime.utcnow()
            }
        )

    async def execute_workflow(
        self,
        workflow_id: int,
        context: Optional[Dict] = None
    ) -> Dict:
        """Execute a workflow."""
        workflow = await self.get_workflow(workflow_id)
        
        if not workflow.is_active:
            raise ValueError("Cannot execute inactive workflow")

        execution_results = []
        current_context = context or {}

        try:
            for step in workflow.steps:
                step_result = await self._execute_workflow_step(step, current_context)
                execution_results.append(step_result)
                # Update context with step results
                current_context.update(step_result.get("output", {}))

            await self._repository.update_workflow(
                workflow_id,
                {
                    "last_execution": datetime.utcnow(),
                    "last_execution_status": "success",
                    "last_execution_results": execution_results
                }
            )

            return {
                "status": "success",
                "results": execution_results,
                "context": current_context
            }

        except Exception as e:
            error_info = {
                "error": str(e),
                "step_results": execution_results
            }
            
            await self._repository.update_workflow(
                workflow_id,
                {
                    "last_execution": datetime.utcnow(),
                    "last_execution_status": "failed",
                    "last_execution_results": error_info
                }
            )
            
            raise

    async def _execute_workflow_step(
        self,
        step: Dict,
        context: Dict
    ) -> Dict:
        """Execute a single workflow step."""
        # This would contain the actual implementation for executing different types of steps
        # For now, we'll return a placeholder result
        return {
            "step_type": step["type"],
            "action": step["action"],
            "status": "completed",
            "output": {}
        }

    async def get_workflow_execution_history(
        self,
        workflow_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """Get execution history for a workflow."""
        workflow = await self.get_workflow(workflow_id)
        return workflow.execution_history[:limit] if workflow.execution_history else []

    async def create_task_workflow(
        self,
        user_id: int,
        name: str,
        task_steps: List[Dict],
        description: Optional[str] = None
    ) -> Workflow:
        """Create a task-based workflow."""
        return await self._repository.create_task_workflow(
            user_id,
            name,
            task_steps,
            description
        )

    async def create_automation_workflow(
        self,
        user_id: int,
        name: str,
        automation_steps: List[Dict],
        triggers: List[Dict],
        description: Optional[str] = None
    ) -> Workflow:
        """Create an automation workflow."""
        return await self._repository.create_automation_workflow(
            user_id,
            name,
            automation_steps,
            triggers,
            description
        )

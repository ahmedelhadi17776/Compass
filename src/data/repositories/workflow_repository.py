"""Workflow repository module."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.workflow import Workflow
from core.exceptions import WorkflowNotFoundError

class WorkflowRepository:
    """Workflow repository class."""

    def __init__(self, session: AsyncSession):
        """Initialize workflow repository."""
        self._session = session

    async def create_workflow(self, workflow_data: dict) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(
            user_id=workflow_data["user_id"],
            name=workflow_data["name"],
            description=workflow_data.get("description"),
            steps=workflow_data["steps"],
            status=workflow_data.get("status", "draft"),
            is_active=workflow_data.get("is_active", True),
            created_at=datetime.utcnow()
        )
        self._session.add(workflow)
        await self._session.commit()
        await self._session.refresh(workflow)
        return workflow

    async def get_workflow(self, workflow_id: int) -> Workflow:
        """Get a specific workflow."""
        workflow = await self._session.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        workflow = workflow.scalar_one_or_none()
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow with id {workflow_id} not found")
        return workflow

    async def get_user_workflows(
        self,
        user_id: int,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50
    ) -> List[Workflow]:
        """Get workflows for a specific user."""
        query = select(Workflow).where(Workflow.user_id == user_id)
        
        if status:
            query = query.where(Workflow.status == status)
        if is_active is not None:
            query = query.where(Workflow.is_active == is_active)
            
        query = query.order_by(desc(Workflow.created_at)).limit(limit)
        workflows = await self._session.execute(query)
        return workflows.scalars().all()

    async def update_workflow(
        self, workflow_id: int, workflow_data: dict
    ) -> Workflow:
        """Update workflow details."""
        workflow = await self.get_workflow(workflow_id)
        
        for key, value in workflow_data.items():
            if hasattr(workflow, key) and value is not None:
                setattr(workflow, key, value)
        
        workflow.updated_at = datetime.utcnow()
        await self._session.commit()
        await self._session.refresh(workflow)
        return workflow

    async def update_workflow_status(
        self, workflow_id: int, status: str
    ) -> Workflow:
        """Update workflow status."""
        return await self.update_workflow(workflow_id, {"status": status})

    async def toggle_workflow_active(
        self, workflow_id: int, is_active: bool
    ) -> Workflow:
        """Toggle workflow active status."""
        return await self.update_workflow(workflow_id, {"is_active": is_active})

    async def delete_workflow(self, workflow_id: int) -> None:
        """Delete a workflow."""
        workflow = await self.get_workflow(workflow_id)
        await self._session.delete(workflow)
        await self._session.commit()

    async def get_active_workflows(
        self, user_id: Optional[int] = None
    ) -> List[Workflow]:
        """Get active workflows."""
        query = select(Workflow).where(Workflow.is_active == True)
        
        if user_id:
            query = query.where(Workflow.user_id == user_id)
            
        query = query.order_by(desc(Workflow.created_at))
        workflows = await self._session.execute(query)
        return workflows.scalars().all()

    async def create_task_workflow(
        self,
        user_id: int,
        name: str,
        task_steps: List[dict],
        description: Optional[str] = None
    ) -> Workflow:
        """Create a task-based workflow."""
        return await self.create_workflow({
            "user_id": user_id,
            "name": name,
            "description": description,
            "steps": task_steps,
            "type": "task_based"
        })

    async def create_automation_workflow(
        self,
        user_id: int,
        name: str,
        automation_steps: List[dict],
        triggers: List[dict],
        description: Optional[str] = None
    ) -> Workflow:
        """Create an automation workflow."""
        return await self.create_workflow({
            "user_id": user_id,
            "name": name,
            "description": description,
            "steps": automation_steps,
            "triggers": triggers,
            "type": "automation"
        })

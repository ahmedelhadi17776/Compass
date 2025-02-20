from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from Backend.data_layer.database.models.workflow import Workflow, WorkflowStatus
from Backend.data_layer.database.models.user import User
from Backend.data_layer.database.models.organization import Organization
from typing import List, Optional, Dict, cast, Sequence
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, joinedload
from Backend.data_layer.database.models.workflow_step import WorkflowStep
from Backend.data_layer.database.models.workflow_execution import WorkflowExecution, WorkflowStepExecution
from datetime import datetime


class WorkflowRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_workflow(self, **workflow_data) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(**workflow_data)
        self.db_session.add(workflow)
        await self.db_session.commit()
        await self.db_session.refresh(workflow)
        return workflow

    async def create_workflow_step(self, **step_data) -> WorkflowStep:
        """Create a new workflow step."""
        step = WorkflowStep(**step_data)
        self.db_session.add(step)
        await self.db_session.commit()
        await self.db_session.refresh(step)
        return step

    async def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Get a workflow by ID."""
        result = await self.db_session.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def get_workflow_with_metrics(self, workflow_id: int) -> Optional[Workflow]:
        """Get a workflow with all its metrics and related data."""
        result = await self.db_session.execute(
            select(Workflow)
            .where(Workflow.id == workflow_id)
            .options(
                joinedload(Workflow.steps),
                joinedload(Workflow.executions),
                joinedload(Workflow.agent_links)
            )
        )
        return result.unique().scalar_one_or_none()

    async def get_workflow_step(self, step_id: int) -> Optional[WorkflowStep]:
        """Get a workflow step by ID."""
        result = await self.db_session.execute(
            select(WorkflowStep).where(WorkflowStep.id == step_id)
        )
        return result.scalar_one_or_none()

    async def create_workflow_execution(
        self,
        workflow_id: int,
        status: WorkflowStatus
    ) -> WorkflowExecution:
        """Create a new workflow execution."""
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status=status,
            started_at=datetime.utcnow()
        )
        self.db_session.add(execution)
        await self.db_session.commit()
        await self.db_session.refresh(execution)
        return execution

    async def create_step_execution(
        self,
        execution_id: int,
        step_id: int,
        status: str
    ) -> WorkflowStepExecution:
        """Create a new workflow step execution."""
        step_execution = WorkflowStepExecution(
            execution_id=execution_id,
            step_id=step_id,
            status=status,
            started_at=datetime.utcnow()
        )
        self.db_session.add(step_execution)
        await self.db_session.commit()
        await self.db_session.refresh(step_execution)
        return step_execution

    async def update_workflow(
        self,
        workflow_id: int,
        updates: Dict
    ) -> Optional[Workflow]:
        """Update a workflow."""
        workflow = await self.get_workflow(workflow_id)
        if workflow:
            for key, value in updates.items():
                if value is not None:
                    setattr(workflow, key, value)
            await self.db_session.commit()
            await self.db_session.refresh(workflow)
        return workflow

    async def cancel_active_executions(self, workflow_id: int) -> None:
        """Cancel all active executions for a workflow."""
        # Update executions
        await self.db_session.execute(
            update(WorkflowExecution)
            .where(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.status.in_([
                    WorkflowStatus.PENDING,
                    WorkflowStatus.ACTIVE
                ])
            )
            .values(
                status=WorkflowStatus.CANCELLED,
                completed_at=datetime.utcnow()
            )
        )

        # Get affected execution IDs
        executions_result = await self.db_session.execute(
            select(WorkflowExecution)
            .where(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.status == WorkflowStatus.CANCELLED
            )
        )
        execution_ids = [
            execution.id for execution in executions_result.scalars()]

        # Update step executions
        if execution_ids:
            await self.db_session.execute(
                update(WorkflowStepExecution)
                .where(
                    WorkflowStepExecution.execution_id.in_(execution_ids),
                    WorkflowStepExecution.status.in_(["pending", "active"])
                )
                .values(
                    status="cancelled",
                    completed_at=datetime.utcnow()
                )
            )

        await self.db_session.commit()

    async def get_workflow_executions(
        self,
        workflow_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[WorkflowExecution]:
        """Get workflow executions with pagination."""
        result = await self.db_session.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.workflow_id == workflow_id)
            .order_by(WorkflowExecution.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        executions = result.scalars().all()
        return cast(List[WorkflowExecution], list(executions))

    async def update_workflow_status(self, workflow_id: int, status: str) -> bool:
        try:
            stmt = update(Workflow).where(
                Workflow.id == workflow_id).values(status=status)
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
            raise

    async def get_user_workflows(self, user_id: int) -> List[Workflow]:
        result = await self.db_session.execute(
            select(Workflow)
            .where(Workflow.created_by == user_id)
            .options(selectinload(Workflow.steps))
        )
        workflows = result.scalars().all()
        return cast(List[Workflow], list(workflows))

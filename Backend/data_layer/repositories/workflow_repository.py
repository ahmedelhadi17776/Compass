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
from Backend.data_layer.database.models.workflow_agent_interaction import WorkflowAgentInteraction

#set the logger

import logging
logger = logging.getLogger(__name__)

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

    async def delete_workflow(self, workflow_id: int) -> bool:
        workflow = await self.get_workflow(workflow_id)
        if workflow:
            await self.db_session.delete(workflow)
            await self.db_session.commit()
            return True
        return False
# Add these methods to the existing WorkflowRepository class

async def create_workflow_agent_interaction(self, **interaction_data) -> WorkflowAgentInteraction:
    """Create a new workflow agent interaction."""
    interaction = WorkflowAgentInteraction(**interaction_data)
    self.db_session.add(interaction)
    await self.db_session.commit()
    await self.db_session.refresh(interaction)
    return interaction

async def get_workflow_agent_interactions(
    self,
    workflow_id: int,
    interaction_type: Optional[str] = None
) -> List[WorkflowAgentInteraction]:
    """Get all agent interactions for a workflow."""
    query = select(WorkflowAgentInteraction).where(
        WorkflowAgentInteraction.workflow_id == workflow_id
    )
    if interaction_type:
        query = query.where(WorkflowAgentInteraction.interaction_type == interaction_type)
    result = await self.db_session.execute(query)
    return list(result.scalars().all())

async def update_workflow_ai_state(
    self,
    workflow_id: int,
    ai_state: Dict
) -> Optional[Workflow]:
    """Update AI-related state for a workflow."""
    workflow = await self.get_workflow(workflow_id)
    if workflow:
        workflow.ai_enabled = ai_state.get('enabled', workflow.ai_enabled)
        workflow.ai_confidence_threshold = ai_state.get('confidence_threshold', workflow.ai_confidence_threshold)
        workflow.ai_override_rules = ai_state.get('override_rules', workflow.ai_override_rules)
        workflow.ai_learning_data = ai_state.get('learning_data', workflow.ai_learning_data)
        await self.db_session.commit()
        await self.db_session.refresh(workflow)
    return workflow

async def track_workflow_optimization(
    self,
    workflow_id: int,
    optimization_data: Dict
) -> Optional[WorkflowAgentInteraction]:
    """Track workflow optimization attempts."""
    try:
        interaction = WorkflowAgentInteraction(
            workflow_id=workflow_id,
            interaction_type="optimization",
            confidence_score=optimization_data.get('confidence_score'),
            input_data=optimization_data.get('input_data'),
            output_data=optimization_data.get('output_data'),
            performance_metrics=optimization_data.get('performance_metrics'),
            optimization_suggestions=optimization_data.get('suggestions')
        )
        self.db_session.add(interaction)
        await self.db_session.commit()
        await self.db_session.refresh(interaction)
        return interaction
    except Exception as e:
        logger.error(f"Error tracking workflow optimization: {str(e)}")
        await self.db_session.rollback()
        return None

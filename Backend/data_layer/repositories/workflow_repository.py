from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_
from Backend.data_layer.database.models.workflow import Workflow, WorkflowStatus
from Backend.data_layer.database.models.user import User
from Backend.data_layer.database.models.organization import Organization
from typing import List, Optional, Dict, cast, Sequence
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, joinedload
from Backend.data_layer.database.models.workflow_step import WorkflowStep, StepStatus
from Backend.data_layer.database.models.workflow_execution import WorkflowExecution, WorkflowStepExecution
from Backend.data_layer.database.models.workflow_transition import WorkflowTransition
from datetime import datetime
from Backend.data_layer.database.models.workflow_agent_interaction import WorkflowAgentInteraction

# set the logger

import logging
logger = logging.getLogger(__name__)


class WorkflowRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_workflow_transition(self, **transition_data) -> WorkflowTransition:
        """Create a new workflow transition."""
        try:
            transition = WorkflowTransition(**transition_data)
            self.db_session.add(transition)
            await self.db_session.commit()
            await self.db_session.refresh(transition)
            return transition
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error creating workflow transition: {str(e)}")
            raise

    async def get_workflow_transitions(self, workflow_id: int) -> List[WorkflowTransition]:
        """Get all transitions for a workflow's steps."""
        try:
            # First get all step IDs for the workflow
            steps_result = await self.db_session.execute(
                select(WorkflowStep.id).where(
                    WorkflowStep.workflow_id == workflow_id)
            )
            step_ids = [step_id for (step_id,) in steps_result]

            # Then get all transitions involving these steps
            result = await self.db_session.execute(
                select(WorkflowTransition)
                .where(
                    or_(
                        WorkflowTransition.from_step_id.in_(step_ids),
                        WorkflowTransition.to_step_id.in_(step_ids)
                    )
                )
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting workflow transitions: {str(e)}")
            raise

    async def create_workflow(self, **workflow_data) -> Workflow:
        """Create a new workflow."""
        try:
            # Ensure status is properly handled if it's an enum
            if 'status' in workflow_data and hasattr(workflow_data['status'], 'value'):
                workflow_data['status'] = workflow_data['status'].value
                
            # Ensure workflow_type is properly handled if it's an enum
            if 'workflow_type' in workflow_data and hasattr(workflow_data['workflow_type'], 'value'):
                workflow_data['workflow_type'] = workflow_data['workflow_type'].value
                
            workflow = Workflow(**workflow_data)
            self.db_session.add(workflow)
            await self.db_session.commit()
            await self.db_session.refresh(workflow)
            return workflow
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error creating workflow: {str(e)}")
            raise

    async def create_workflow_step(self, **step_data) -> WorkflowStep:
        """Create a new workflow step."""
        try:
            # Handle enum values for step_type
            if 'step_type' in step_data:
                if isinstance(step_data['step_type'], str):
                    from Backend.data_layer.database.models.workflow_step import StepType
                    # Convert uppercase string to lowercase for PostgreSQL enum
                    if step_data['step_type'] == 'MANUAL':
                        step_data['step_type'] = StepType.MANUAL
                    elif step_data['step_type'] == 'AUTOMATED':
                        step_data['step_type'] = StepType.AUTOMATED
                    elif step_data['step_type'] == 'APPROVAL':
                        step_data['step_type'] = StepType.APPROVAL
                    elif step_data['step_type'] == 'NOTIFICATION':
                        step_data['step_type'] = StepType.NOTIFICATION
                    elif step_data['step_type'] == 'INTEGRATION':
                        step_data['step_type'] = StepType.INTEGRATION
                    elif step_data['step_type'] == 'DECISION':
                        step_data['step_type'] = StepType.DECISION
                    elif step_data['step_type'] == 'AI_TASK':
                        step_data['step_type'] = StepType.AI_TASK
            
            # Handle enum values for status
            if 'status' in step_data and isinstance(step_data['status'], str):
                from Backend.data_layer.database.models.workflow_step import StepStatus
                if step_data['status'] == 'PENDING':
                    step_data['status'] = StepStatus.PENDING
                elif step_data['status'] == 'ACTIVE':
                    step_data['status'] = StepStatus.ACTIVE
                elif step_data['status'] == 'COMPLETED':
                    step_data['status'] = StepStatus.COMPLETED
                elif step_data['status'] == 'SKIPPED':
                    step_data['status'] = StepStatus.SKIPPED
                elif step_data['status'] == 'FAILED':
                    step_data['status'] = StepStatus.FAILED
            
            step = WorkflowStep(**step_data)
            self.db_session.add(step)
            await self.db_session.commit()
            await self.db_session.refresh(step)
            return step
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error creating workflow step: {str(e)}")
            raise

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
        status: str,
        execution_metadata: Optional[Dict] = None
    ) -> WorkflowStepExecution:
        """Create a new workflow step execution with metadata tracking."""
        try:
            step_execution = WorkflowStepExecution(
                execution_id=execution_id,
                step_id=step_id,
                status=status,
                execution_metadata=execution_metadata or {},
                started_at=datetime.utcnow()
            )
            self.db_session.add(step_execution)
            await self.db_session.commit()
            await self.db_session.refresh(step_execution)
            return step_execution
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error creating step execution: {str(e)}")
            raise

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

    async def create_workflow_agent_interaction(self, **interaction_data) -> WorkflowAgentInteraction:
        """Create a new workflow agent interaction."""
        try:
            interaction = WorkflowAgentInteraction(**interaction_data)
            self.db_session.add(interaction)
            await self.db_session.commit()
            await self.db_session.refresh(interaction)
            return interaction
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error creating workflow agent interaction: {str(e)}")
            raise

    async def get_workflow_agent_interactions(
        self,
        workflow_id: int,
        interaction_type: Optional[str] = None
    ) -> List[WorkflowAgentInteraction]:
        """Get all agent interactions for a workflow."""
        try:
            query = select(WorkflowAgentInteraction).where(
                WorkflowAgentInteraction.workflow_id == workflow_id
            )
            if interaction_type:
                query = query.where(
                    WorkflowAgentInteraction.interaction_type == interaction_type)
            result = await self.db_session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting workflow agent interactions: {str(e)}")
            raise

    async def update_workflow_ai_state(
        self,
        workflow_id: int,
        ai_state: Dict
    ) -> Optional[Workflow]:
        """Update AI-related state for a workflow."""
        try:
            workflow = await self.get_workflow(workflow_id)
            if workflow:
                workflow.ai_enabled = ai_state.get('enabled', workflow.ai_enabled)
                workflow.ai_confidence_threshold = ai_state.get(
                    'confidence_threshold', workflow.ai_confidence_threshold)
                workflow.ai_override_rules = ai_state.get(
                    'override_rules', workflow.ai_override_rules)
                workflow.ai_learning_data = ai_state.get(
                    'learning_data', workflow.ai_learning_data)
                await self.db_session.commit()
                await self.db_session.refresh(workflow)
            return workflow
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error updating workflow AI state: {str(e)}")
            raise

    async def update_step_execution(
        self,
        execution_id: int,
        step_id: int,
        status: str,
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ) -> Optional[WorkflowStepExecution]:
        """Update a workflow step execution status and result."""
        try:
            is_terminal_status = status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]
            
            stmt = (
                update(WorkflowStepExecution)
                .where(
                    WorkflowStepExecution.execution_id == execution_id,
                    WorkflowStepExecution.step_id == step_id
                )
                .values(
                    status=status,
                    result=result,
                    error=error,
                    completed_at=datetime.utcnow() if is_terminal_status else None
                )
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()

            # Return updated execution
            result = await self.db_session.execute(
                select(WorkflowStepExecution)
                .where(
                    WorkflowStepExecution.execution_id == execution_id,
                    WorkflowStepExecution.step_id == step_id
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error updating step execution: {str(e)}")
            return None

    async def track_workflow_optimization(
        self,
        workflow_id: int,
        optimization_data: Dict
    ) -> Optional[WorkflowAgentInteraction]:
        """Track workflow optimization attempts."""
        try:
            # Validate required fields
            if not workflow_id or not optimization_data:
                logger.error(
                    "Missing required fields for workflow optimization tracking")
                return None

            # Ensure workflow exists
            workflow = await self.get_workflow(workflow_id)
            if not workflow:
                logger.error(f"Workflow {workflow_id} not found")
                return None

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

            # Update workflow optimization score if provided
            if 'optimization_score' in optimization_data:
                await self.update_workflow(
                    workflow_id,
                    {'optimization_score': optimization_data['optimization_score']}
                )

            return interaction
        except IntegrityError as ie:
            logger.error(f"Database integrity error: {str(ie)}")
            await self.db_session.rollback()
            return None
        except Exception as e:
            logger.error(f"Error tracking workflow optimization: {str(e)}")
            await self.db_session.rollback()
            return None

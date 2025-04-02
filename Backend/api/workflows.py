from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, ValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from Backend.data_layer.database.connection import get_db
from Backend.services.workflow_service import WorkflowService
from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
from Backend.app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse,
    WorkflowDetail, WorkflowMetrics
)
from Backend.api.auth import get_current_user

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow: WorkflowCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new workflow with AI optimization."""
    try:
        repo = WorkflowRepository(db)
        service = WorkflowService(repo)
        
        # Extract workflow data from the schema
        workflow_data = workflow.dict(exclude_unset=True)
        
        # Replace 'created_by' with 'creator_id' if it exists
        if 'created_by' in workflow_data:
            workflow_data['creator_id'] = workflow_data.pop('created_by')
        else:
            # Add creator_id from the current user
            workflow_data['creator_id'] = current_user.id
            
        # Ensure organization_id is present
        if 'organization_id' not in workflow_data:
            workflow_data['organization_id'] = current_user.organization_id
        
        # Process steps to ensure enum values are properly handled
        if 'steps' in workflow_data and workflow_data['steps']:
            for step in workflow_data['steps']:
                # Convert step_type to lowercase if it's a string
                if 'step_type' in step and isinstance(step['step_type'], str):
                    step['step_type'] = step['step_type'].lower()
                
                # Convert status to lowercase if it's a string
                if 'status' in step and isinstance(step['status'], str):
                    step['status'] = step['status'].lower()
            
        result = await service.create_workflow(**workflow_data)

        # Schedule AI optimization in background if enabled
        if workflow_data.get('ai_enabled', False):
            background_tasks.add_task(
                service.optimize_workflow,
                result['workflow_id']
            )

        return result
    except ValidationError as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/{workflow_id}", response_model=WorkflowDetail)
async def get_workflow(
    workflow_id: int,
    include_metrics: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get workflow details with steps and executions."""
    try:
        repo = WorkflowRepository(db)
        service = WorkflowService(repo)
        
        # Get workflow with details
        workflow = await service.get_workflow_with_details(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow with ID {workflow_id} not found"
            )
            
        return workflow
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflow: {str(e)}"
        )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow_update: WorkflowUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update workflow with AI state tracking."""
    try:
        repo = WorkflowRepository(db)
        service = WorkflowService(repo)

        # Get current workflow state
        current_workflow = await service.get_workflow_with_details(workflow_id)
        if not current_workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Check if user has permission to update
        if current_workflow.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this workflow"
            )

        # Validate state transition
        if workflow_update.status and current_workflow.status != workflow_update.status:
            if not service.is_valid_status_transition(current_workflow.status, workflow_update.status):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status transition from {current_workflow.status} to {workflow_update.status}"
                )

        result = await service.update_workflow(
            workflow_id,
            workflow_update.dict(exclude_unset=True)
        )

        # Track changes in background
        background_tasks.add_task(
            service.track_workflow_changes,
            workflow_id,
            current_user.id,
            workflow_update.dict(exclude_unset=True)
        )

        return result
    except ValidationError as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workflow: {str(e)}"
        )


@router.post("/{workflow_id}/ai-analyze")
async def analyze_workflow(
    workflow_id: int,
    analysis_params: Dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Analyze workflow using AI capabilities."""
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    result = await service.analyze_workflow_with_ai(workflow_id, analysis_params)
    return result


@router.post("/{workflow_id}/optimize")
async def optimize_workflow(
    workflow_id: int,
    optimization_params: Dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Optimize workflow using AI agents."""
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    result = await service.optimize_workflow(workflow_id, optimization_params)
    return result


@router.get("/{workflow_id}/agent-interactions")
async def get_workflow_agent_interactions(
    workflow_id: int,
    interaction_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all agent interactions for a workflow."""
    repo = WorkflowRepository(db)
    interactions = await repo.get_workflow_agent_interactions(
        workflow_id,
        interaction_type=interaction_type
    )
    return interactions


@router.get("/{workflow_id}/metrics", response_model=WorkflowMetrics)
async def get_workflow_metrics(
    workflow_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get workflow performance metrics."""
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    metrics = await service.get_workflow_metrics(
        workflow_id,
        start_date=start_date,
        end_date=end_date
    )
    if not metrics:
        raise HTTPException(
            status_code=404, detail="Workflow metrics not found")
    return metrics


@router.post("/{workflow_id}/agent-interaction")
async def create_workflow_agent_interaction(
    workflow_id: int,
    interaction_data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Record a new agent interaction with the workflow."""
    repo = WorkflowRepository(db)
    interaction = await repo.create_workflow_agent_interaction(
        workflow_id=workflow_id,
        user_id=current_user.id,
        **interaction_data
    )
    return interaction


@router.get("/{workflow_id}/ai-insights")
async def get_workflow_ai_insights(
    workflow_id: int,
    metric_types: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get AI-generated insights for the workflow."""
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    insights = await service.get_workflow_ai_insights(workflow_id, metric_types)
    return insights

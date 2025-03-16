from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new workflow with AI optimization."""
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    result = await service.create_workflow(
        creator_id=current_user.id,
        **workflow.dict()
    )
    return result

@router.get("/{workflow_id}", response_model=WorkflowDetail)
async def get_workflow(
    workflow_id: int,
    include_metrics: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get workflow details with optional metrics."""
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    workflow = await service.get_workflow_with_details(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow_update: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update workflow with AI state tracking."""
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    result = await service.update_workflow(workflow_id, workflow_update.dict(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result

@router.post("/{workflow_id}/ai-analyze")
async def analyze_workflow(
    workflow_id: int,
    analysis_params: Dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
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
        raise HTTPException(status_code=404, detail="Workflow metrics not found")
    return metrics

@router.post("/{workflow_id}/agent-interaction")
async def create_workflow_agent_interaction(
    workflow_id: int,
    interaction_data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
):
    """Get AI-generated insights for the workflow."""
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    insights = await service.get_workflow_ai_insights(workflow_id, metric_types)
    return insights

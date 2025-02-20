from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.data_layer.database.connection import get_db
from Backend.services.workflow_service import WorkflowService
from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
from typing import Dict, List
from pydantic import BaseModel

router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowCreate(BaseModel):
    user_id: int
    organization_id: int
    name: str
    description: str
    steps: List[Dict]


class WorkflowStepExecute(BaseModel):
    user_id: int
    input_data: Dict


class WorkflowAnalyze(BaseModel):
    user_id: int
    analysis_type: str
    time_range: str
    metrics: List[str]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow: WorkflowCreate,
    db: AsyncSession = Depends(get_db)
):
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    result = await service.create_workflow(
        user_id=workflow.user_id,
        organization_id=workflow.organization_id,
        name=workflow.name,
        description=workflow.description,
        steps=workflow.steps
    )
    return result


@router.post("/{workflow_id}/steps/{step_id}/execute")
async def execute_workflow_step(
    workflow_id: int,
    step_id: int,
    data: WorkflowStepExecute,
    db: AsyncSession = Depends(get_db)
):
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    result = await service.execute_step(
        workflow_id=workflow_id,
        step_id=step_id,
        user_id=data.user_id,
        input_data=data.input_data
    )
    return result


@router.post("/{workflow_id}/analyze")
async def analyze_workflow(
    workflow_id: int,
    data: WorkflowAnalyze,
    db: AsyncSession = Depends(get_db)
):
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    result = await service.analyze_workflow(
        workflow_id=workflow_id,
        user_id=data.user_id,
        analysis_type=data.analysis_type,
        time_range=data.time_range,
        metrics=data.metrics
    )
    return result


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    result = await service.get_task_status(task_id)
    return result


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    repo = WorkflowRepository(db)
    service = WorkflowService(repo)
    result = await service.cancel_workflow(
        workflow_id=workflow_id,
        user_id=data["user_id"]
    )
    return result

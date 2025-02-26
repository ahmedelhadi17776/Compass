from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List
from datetime import datetime

from Backend.data_layer.database.connection import get_db
from Backend.app.schemas.task_schemas import TaskCreate, TaskResponse
from Backend.services.ai_service import AIService
from Backend.core.rbac import get_current_user
from Backend.data_layer.database.models.ai_interactions import AIAgentInteraction

router = APIRouter(prefix="/ai", tags=["AI Services"])

# Initialize centralized AI service
ai_service = AIService()

@router.post("/analyze/task")
async def analyze_task(
    task_data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Analyze task using AI agents."""
    try:
        result = await ai_service.process_task_with_ai(
            task_data=task_data,
            task_id=task_data.get("id"),
            process_type="analysis"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/productivity/{user_id}")
async def get_productivity_insights(
    user_id: int,
    interval: str = "daily",
    metrics: List[str] = ["focus", "efficiency", "workload"],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get AI-generated productivity insights."""
    try:
        # Use AIService to get tasks and analyze productivity
        tasks = await ai_service.get_user_tasks(user_id, db)
        insights = await ai_service.analyze_productivity(tasks, interval)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/classify-task")
async def classify_task(
    task_data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Classify a task using AI."""
    try:
        return await ai_service.classify_task(task_data, db, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-text")
async def analyze_text(
    text: str,
    analysis_type: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Analyze text using different AI services."""
    try:
        return await ai_service.analyze_text(text, analysis_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-productivity")
async def analyze_productivity(
    tasks: List[Dict],
    time_period: str = "daily",
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Analyze task productivity patterns."""
    try:
        return await ai_service.analyze_productivity(tasks, time_period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize")
async def summarize_text(
    text: str,
    max_length: int = 130,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate text summary."""
    try:
        result = await ai_service.summarization_service.generate_summary(text, max_length)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback/{interaction_id}")
async def submit_ai_feedback(
    interaction_id: int,
    feedback_score: float,
    feedback_text: str = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Submit feedback for an AI interaction."""
    try:
        # Use AIService to handle feedback submission
        return await ai_service.submit_feedback(
            interaction_id=interaction_id,
            feedback_score=feedback_score,
            feedback_text=feedback_text,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
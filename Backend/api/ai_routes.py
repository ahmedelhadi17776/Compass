from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List
from Backend.data_layer.database.connection import get_db
from Backend.ai_services.task_ai.task_classification_service import TaskClassificationService
from Backend.ai_services.emotion_ai.emotion_service import EmotionService
from Backend.ai_services.nlp_service.nlp_service import NLPService
from Backend.ai_services.productivity_ai.productivity_service import ProductivityService
from Backend.ai_services.summarization_engine.summarization_service import SummarizationService
from Backend.core.rbac import get_current_user
from Backend.orchestration.crew_orchestrator import CrewOrchestrator
from Backend.tasks.ai_tasks import process_task_analysis

router = APIRouter(prefix="/ai", tags=["AI Services"])

@router.post("/analyze/task")
async def analyze_task(
    task_data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Analyze task using AI agents."""
    try:
        # Queue task analysis
        result = await process_task_analysis.delay(task_data)
        return {
            "task_id": task_data.get("id"),
            "analysis_job_id": result.id,
            "status": "queued"
        }
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
        orchestrator = CrewOrchestrator()
        insights = await orchestrator.analyze_productivity(user_id, interval, metrics)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Service instances
task_classifier = TaskClassificationService()
emotion_service = EmotionService()
nlp_service = NLPService()
productivity_service = ProductivityService()
summarization_service = SummarizationService()

@router.post("/classify-task")
async def classify_task(task_data: Dict):
    """Classify a task using AI."""
    return await task_classifier.classify_task(task_data)

@router.post("/analyze-text")
async def analyze_text(text: str, analysis_type: str):
    """Analyze text using different AI services."""
    try:
        results = {}
        if analysis_type in ["all", "sentiment"]:
            results["sentiment"] = await nlp_service.analyze_sentiment(text)
        if analysis_type in ["all", "emotion"]:
            results["emotion"] = await emotion_service.analyze_emotion(text)
        if analysis_type in ["all", "summary"]:
            results["summary"] = await summarization_service.generate_summary(text)
        if analysis_type in ["all", "keywords"]:
            results["keywords"] = await nlp_service.extract_keywords(text)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-productivity")
async def analyze_productivity(tasks: List[Dict], time_period: str = "daily"):
    """Analyze task productivity patterns."""
    return await productivity_service.analyze_task_patterns(tasks, time_period)

@router.post("/summarize")
async def summarize_text(text: str, max_length: int = 130):
    """Generate text summary."""
    return await summarization_service.generate_summary(text, max_length)
@router.post("/feedback/{interaction_id}")
async def submit_ai_feedback(
    interaction_id: int,
    feedback_score: float,
    feedback_text: str = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Submit feedback for an AI interaction."""
    try:
        interaction = await db.get(AIAgentInteraction, interaction_id)
        if not interaction:
            raise HTTPException(status_code=404, detail="Interaction not found")
        
        interaction.feedback_score = feedback_score
        interaction.improvement_suggestions = feedback_text
        interaction.was_helpful = feedback_score >= 0.7
        
        await db.commit()
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
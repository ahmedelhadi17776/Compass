from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging
import os
from openai import OpenAI
from fastapi import Request, BackgroundTasks

from Backend.data_layer.database.connection import get_db
from Backend.app.schemas.task_schemas import TaskCreate, TaskResponse
from Backend.services.ai_service import AIService
from Backend.api.auth import get_current_user
from Backend.data_layer.database.models.ai_interactions import AIAgentInteraction
from Backend.ai_services.llm.llm_service import LLMService
from Backend.data_layer.database.models.user import User
from Backend.ai_services.rag.todo_ai_service import TodoAIService
from Backend.orchestration.ai_orchestrator import AIOrchestrator


# Set up logger
logger = logging.getLogger(__name__)

# Request/Response Models

class PreviousMessage(BaseModel):
    sender: str
    text: str

class AIRequest(BaseModel):
    prompt: str
    context: Optional[Dict] = None
    domain: Optional[str] = None
    model_parameters: Optional[Dict] = None
    previous_messages: Optional[List[PreviousMessage]] = None


class AIResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    target: Optional[str] = None
    description: Optional[str] = None
    rag_used: bool = False
    cached: bool = False
    confidence: float = 0.0
    error: Optional[bool] = None
    error_message: Optional[str] = None


class FeedbackRequest(BaseModel):
    feedback_score: float = Field(..., ge=0, le=1)
    feedback_text: Optional[str] = None


router = APIRouter(prefix="/ai", tags=["AI Services"])

# Initialize services
ai_service = AIService()
llm_service = LLMService()
todo_ai_service = TodoAIService()


@router.post("/process", response_model=AIResponse)
async def process_ai_request(
    request: AIRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process an AI request through the orchestration layer.

    Flow:
    1. Context Building
    2. Reference Resolution
    3. Intent Detection
    4. Cache Check
    5. RAG Processing
    6. Template Rendering
    7. LLM Response Generation
    8. Result Caching
    """
    try:
        orchestrator = AIOrchestrator(db)
        
        # If we have previous messages from the frontend, add them to the conversation history
        if request.previous_messages:
            for msg in request.previous_messages:
                if msg.sender == "user":
                    user_message = {"role": "user", "content": msg.text}
                    if current_user.id not in orchestrator.conversation_history:
                        orchestrator.conversation_history[current_user.id] = []
                    orchestrator.conversation_history[current_user.id].append(user_message)
                elif msg.sender == "assistant":
                    assistant_message = {"role": "assistant", "content": msg.text}
                    if current_user.id not in orchestrator.conversation_history:
                        orchestrator.conversation_history[current_user.id] = []
                    orchestrator.conversation_history[current_user.id].append(assistant_message)
        
        result = await orchestrator.process_request(
            user_input=request.prompt,
            user_id=current_user.id,
            domain=request.domain
        )

        # Transform the result to match AIResponse model
        response_data = {
            "response": result.get("response", ""),
            "intent": result.get("intent"),
            "target": result.get("target"),
            "description": result.get("description"),
            "rag_used": result.get("rag_used", False),
            "cached": result.get("cached", False),
            "confidence": result.get("confidence", 0.0),
            "error": False,
            "error_message": None
        }

        return AIResponse(**response_data)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing AI request: {error_msg}")
        return AIResponse(
            response="",
            error=True,
            error_message=error_msg,
            cached=False,
            rag_used=False,
            confidence=0.0
        )


@router.post("/process/stream")
async def process_ai_request_stream(
    request: AIRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stream AI responses for real-time interaction."""
    try:
        # Initialize the streaming response
        orchestrator = AIOrchestrator(db)
        
        # If we have previous messages from the frontend, add them to the conversation history
        if request.previous_messages:
            for msg in request.previous_messages:
                if msg.sender == "user":
                    user_message = {"role": "user", "content": msg.text}
                    if current_user.id not in orchestrator.conversation_history:
                        orchestrator.conversation_history[current_user.id] = []
                    orchestrator.conversation_history[current_user.id].append(user_message)
                elif msg.sender == "assistant":
                    assistant_message = {"role": "assistant", "content": msg.text}
                    if current_user.id not in orchestrator.conversation_history:
                        orchestrator.conversation_history[current_user.id] = []
                    orchestrator.conversation_history[current_user.id].append(assistant_message)
        
        async def stream_generator():
            try:
                # Use the orchestrator to process in streaming mode
                stream = await llm_service.generate_response(
                    prompt=request.prompt,
                    stream=True
                )
                
                async for chunk in stream:
                    yield f"data: {chunk}\n\n"
                    
                yield "data: [DONE]\n\n"
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error in stream: {error_msg}")
                yield f"data: Error: {error_msg}\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error setting up stream: {error_msg}")
        return StreamingResponse(
            iter([f"data: Error: {error_msg}\n\n"]),
            media_type="text/event-stream"
        )

@router.get("/context/{user_id}")
async def get_user_context(
    user_id: int,
    domains: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the full context for a user across specified domains."""
    try:
        orchestrator = AIOrchestrator(db)
        context = await orchestrator.context_builder.get_full_context(user_id, domains)
        return {"context": context}
    except Exception as e:
        logger.error(f"Error getting user context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/{interaction_id}")
async def submit_ai_feedback(
    interaction_id: int,
    feedback: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit feedback for an AI interaction."""
    try:
        return await ai_service.submit_feedback(
            interaction_id=interaction_id,
            feedback_score=feedback.feedback_score,
            feedback_text=feedback.feedback_text,
            db=db
        )
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI cache statistics."""
    try:
        orchestrator = AIOrchestrator(db)
        cache_config = orchestrator.ai_registry.get_cache_config()
        return {
            "config": cache_config,
            "enabled": cache_config.get("enabled", False),
            "ttl_settings": cache_config.get("ttl_per_intent", {})
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/stats/{domain}")
async def get_rag_stats(
    domain: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get RAG statistics for a specific domain."""
    try:
        orchestrator = AIOrchestrator(db)
        rag_settings = orchestrator.ai_registry.get_rag_settings(domain)
        collection_stats = await orchestrator.rag_service.get_collection_stats(domain)
        return {
            "settings": rag_settings,
            "collection_stats": collection_stats
        }
    except Exception as e:
        logger.error(f"Error getting RAG stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/update/{domain}")
async def update_rag_knowledge(
    domain: str,
    content: Dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the RAG knowledge base for a domain."""
    try:
        orchestrator = AIOrchestrator(db)
        await orchestrator.rag_service.add_to_knowledge_base(
            domain=domain,
            content=content
        )
        return {"status": "success", "message": f"Knowledge base updated for domain: {domain}"}
    except Exception as e:
        logger.error(f"Error updating RAG knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/info")
async def get_model_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get information about the AI model configuration."""
    try:
        orchestrator = AIOrchestrator(db)
        model_id = await orchestrator._get_or_create_model()
        if not model_id:
            raise HTTPException(status_code=404, detail="Model not found")

        model = await orchestrator.model_repository.get_model_by_id(model_id)
        return {
            "model_id": model_id,
            "model_info": model.model_metadata if model else None,
            "llm_config": orchestrator.ai_registry.llm_config
        }
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/knowledge-base/process", response_model=Dict[str, Any], status_code=202)
async def process_knowledge_base(
    request: Request,
    background_tasks: BackgroundTasks,
    domain: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Process knowledge base files into the RAG system."""
    try:
        # Get the path to the knowledge base directory
        kb_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ai_services", "rag", "knowledge_base"
        )

        # Import the processor here to avoid circular imports
        from Backend.ai_services.rag.knowledge_processor import process_knowledge_base

        # Add task to background processing
        background_tasks.add_task(process_knowledge_base, kb_dir)

        return {
            "status": "processing",
            "message": "Knowledge base processing started in the background"
        }
    except Exception as e:
        logger.error(f"Error starting knowledge base processing: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing knowledge base: {str(e)}")

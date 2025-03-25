from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any, cast, Union
from datetime import datetime
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging
import os
import shutil
from pathlib import Path
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam
from fastapi import Request, BackgroundTasks
from sqlalchemy import Column
import json

from Backend.data_layer.database.connection import get_db
from Backend.app.schemas.task_schemas import TaskCreate, TaskResponse
from Backend.services.ai_service import AIService
from Backend.api.auth import get_current_user
from Backend.data_layer.database.models.ai_interactions import AIAgentInteraction
from Backend.ai_services.llm.llm_service import LLMService
from Backend.data_layer.database.models.user import User
from Backend.orchestration.ai_orchestrator import AIOrchestrator
from Backend.app.schemas.message_schemas import UserMessage, AssistantMessage, ConversationHistory


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


class ProcessPDFResponse(BaseModel):
    status: str
    message: str
    processed_files: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


router = APIRouter(prefix="/ai", tags=["AI Services"])

# Initialize services
ai_service = AIService()
llm_service = LLMService()

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

        # Get user ID safely
        if not hasattr(current_user, 'id'):
            raise ValueError("User ID is required")

        # Convert SQLAlchemy Column to string then int
        user_id = int(str(getattr(current_user, 'id')))

        # Process previous messages
        if request.previous_messages:
            # Get or create conversation history
            history = orchestrator._get_conversation_history(user_id)

            # Add messages to history
            for msg in request.previous_messages:
                if msg.sender == "user":
                    history.add_message(UserMessage(content=str(msg.text)))
                elif msg.sender == "assistant":
                    history.add_message(
                        AssistantMessage(content=str(msg.text)))

        result = await orchestrator.process_request(
            user_input=request.prompt,
            user_id=user_id,
            domain=str(request.domain) if request.domain else None
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

        # Get user ID safely
        if not hasattr(current_user, 'id'):
            raise ValueError("User ID is required")

        # Convert SQLAlchemy Column to string then int
        user_id = int(str(getattr(current_user, 'id')))

        # Process previous messages if any
        if request.previous_messages:
            history = orchestrator._get_conversation_history(user_id)
            for msg in request.previous_messages:
                if msg.sender == "user":
                    history.add_message(UserMessage(content=str(msg.text)))
                elif msg.sender == "assistant":
                    history.add_message(
                        AssistantMessage(content=str(msg.text)))

        async def stream_generator():
            try:
                # Check if this is an entity creation request
                intent_result = await orchestrator.intent_detector.detect_intent(
                    request.prompt, 
                    {"tasks": {}, "todos": {}, "habits": {}, "default": {}}
                )
                
                if intent_result.get("intent") == "create":
                    # Handle entity creation
                    entity_type = intent_result.get("target", "task")
                    
                    # First yield a confirmation message
                    confirmation = f"Creating a new {entity_type} based on your description..."
                    yield f"data: {json.dumps({'text': confirmation, 'done': False})}\n\n"
                    
                    # Process the entity creation
                    creation_result = await orchestrator.process_entity_creation(request.prompt, user_id)
                    
                    # Yield the creation result
                    result_message = creation_result.get("response", f"Created {entity_type} successfully")
                    yield f"data: {json.dumps({'text': result_message, 'done': True, 'metadata': {'entity_type': entity_type, 'creation_result': creation_result}})}\n\n"
                    
                    yield "data: [DONE]\n\n"
                    return
                
                # Use the orchestrator to process in streaming mode for non-creation intents
                stream = await orchestrator.llm_service.generate_response(
                    prompt=request.prompt,
                    context={"user_id": user_id, "domain": request.domain} if request.domain else {
                        "user_id": user_id},
                    model_parameters=request.model_parameters,
                    stream=True
                )

                async for chunk in stream:
                    yield f"data: {chunk}\n\n"

                yield "data: [DONE]\n\n"
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error in stream: {error_msg}")
                yield f"data: {json.dumps({'text': f'Error: {error_msg}', 'done': True, 'error': True})}\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error setting up stream: {error_msg}")
        return StreamingResponse(
            iter([f"data: {json.dumps({'text': f'Error: {error_msg}', 'done': True, 'error': True})}\n\n"]),
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
        llm_cache_stats = {
            "hits": orchestrator.llm_service.cache_hits,
            "ttls": orchestrator.llm_service.cache_ttls,
            "hit_threshold": orchestrator.llm_service.cache_hit_threshold
        }
        return {
            "config": cache_config,
            "enabled": cache_config.get("enabled", False),
            "ttl_settings": cache_config.get("ttl_per_intent", {}),
            "llm_cache_stats": llm_cache_stats
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


@router.post("/knowledge-base/upload", response_model=ProcessPDFResponse)
async def upload_pdf_to_knowledge_base(
    file: UploadFile = File(...),
    domain: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a PDF file to the knowledge base."""
    try:
        # Create knowledge base directory if it doesn't exist
        kb_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ai_services", "rag", "knowledge_base"
        )
        os.makedirs(kb_dir, exist_ok=True)

        # Save the uploaded file
        file_path = os.path.join(kb_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the PDF
        from Backend.ai_services.rag.knowledge_processor import process_knowledge_base
        result = await process_knowledge_base(kb_dir)

        return ProcessPDFResponse(
            status="success",
            message=f"PDF processed successfully: {file.filename}",
            processed_files=result.get("files", [])
        )
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )


@router.post("/entity/create", response_model=AIResponse)
async def create_entity(
    request: AIRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new entity (task, todo, habit) from natural language description."""
    try:
        orchestrator = AIOrchestrator(db)

        # Get user ID safely
        if not hasattr(current_user, 'id'):
            raise ValueError("User ID is required")

        # Convert SQLAlchemy Column to string then int
        user_id = int(str(getattr(current_user, 'id')))

        # Process the entity creation
        creation_result = await orchestrator.process_entity_creation(request.prompt, user_id)
        
        return AIResponse(
            response=creation_result.get("response", "Entity created"),
            intent=creation_result.get("intent", "create"),
            target=creation_result.get("target", "unknown"),
            description=creation_result.get("description", "Create entity from description"),
            rag_used=False,
            cached=False,
            confidence=creation_result.get("confidence", 0.9),
            error=creation_result.get("error", False),
            error_message=creation_result.get("error_message")
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error creating entity: {error_msg}")
        return AIResponse(
            response=f"Error creating entity: {error_msg}",
            intent="create",
            target="unknown",
            description="Create entity from description",
            rag_used=False,
            cached=False,
            confidence=0.0,
            error=True,
            error_message=error_msg
        )

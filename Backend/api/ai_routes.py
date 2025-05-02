from fastapi import APIRouter, HTTPException, status, Query, File, UploadFile, Request, BackgroundTasks, Depends, Cookie
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging
import os
import shutil
import json
from pathlib import Path
import uuid

from Backend.ai_services.llm.llm_service import LLMService
from Backend.orchestration.ai_orchestrator import AIOrchestrator
from Backend.app.schemas.message_schemas import UserMessage, AssistantMessage, ConversationHistory
from Backend.core.config import settings
from Backend.core.mcp_state import get_mcp_client

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
    session_id: Optional[str] = None  # Add session ID field


class AIResponse(BaseModel):
    response: str
    tool_used: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_success: Optional[bool] = None
    description: Optional[str] = None
    rag_used: bool = False
    cached: bool = False
    confidence: float = 0.0
    error: Optional[bool] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None  # Add session ID to response


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
llm_service = LLMService()

# Store orchestrators by session ID for persistent conversations
orchestrator_instances: Dict[str, AIOrchestrator] = {}


def get_or_create_orchestrator(session_id: str) -> AIOrchestrator:
    """Get an existing orchestrator or create a new one for the session."""
    if session_id not in orchestrator_instances:
        logger.info(f"Creating new orchestrator for session {session_id}")
        orchestrator_instances[session_id] = AIOrchestrator()
    return orchestrator_instances[session_id]


@router.post("/process", response_model=AIResponse)
async def process_ai_request(
    request: AIRequest,
    session_id: Optional[str] = Cookie(None)
) -> AIResponse:
    """Process an AI request through MCP."""
    try:
        # Get or create session ID
        active_session_id = request.session_id or session_id or str(uuid.uuid4())
        
        # Get or create orchestrator for this session
        orchestrator = get_or_create_orchestrator(active_session_id)
        
        # Map session ID to a numeric user ID for the orchestrator
        # Use a hash of the session ID to get a consistent integer
        user_id = int(hash(active_session_id) % 100000)

        # Process request
        result = await orchestrator.process_request(
            user_input=request.prompt,
            user_id=user_id,  # Use the mapped user ID
            domain=request.domain or "default"
        )
        
        # Add session ID to response
        result["session_id"] = active_session_id
        return AIResponse(**result)
    except Exception as e:
        logger.error(f"Error processing AI request: {str(e)}")
        return AIResponse(
            response=f"Error: {str(e)}",
            tool_used=None,
            tool_args=None,
            tool_success=False,
            description="Error processing request",
            rag_used=False,
            cached=False,
            confidence=0.0,
            error=True,
            error_message=str(e),
            session_id=request.session_id or session_id
        )


@router.get("/rag/stats/{domain}")
async def get_rag_stats(
    domain: str,
):
    """Get RAG statistics for a specific domain through MCP."""
    try:
        mcp_client = get_mcp_client()
        if not mcp_client:
            raise HTTPException(
                status_code=503, detail="MCP client not initialized")

        result = await mcp_client.invoke_tool("rag.stats", {
            "domain": domain
        })
        return result
    except Exception as e:
        logger.error(f"Error getting RAG stats through MCP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/update/{domain}")
async def update_rag_knowledge(
    domain: str,
    content: Dict,
):
    """Update the RAG knowledge base for a domain through MCP."""
    try:
        mcp_client = get_mcp_client()
        if not mcp_client:
            raise HTTPException(
                status_code=503, detail="MCP client not initialized")

        result = await mcp_client.invoke_tool("rag.update", {
            "domain": domain,
            "content": content
        })
        return result
    except Exception as e:
        logger.error(f"Error updating RAG knowledge through MCP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/info")
async def get_model_info():
    """Get information about the AI model configuration through MCP."""
    try:
        mcp_client = get_mcp_client()
        if not mcp_client:
            raise HTTPException(
                status_code=503, detail="MCP client not initialized")

        result = await mcp_client.invoke_tool("ai.model.info", {})
        return result
    except Exception as e:
        logger.error(f"Error getting model info through MCP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-session")
async def clear_session(
    request: Request
):
    """Clear conversation history for a session."""
    try:
        # Parse request body
        data = await request.json()
        session_id = data.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id in request body")
            
        if session_id in orchestrator_instances:
            orchestrator = orchestrator_instances[session_id]
            user_id = int(hash(session_id) % 100000)
            orchestrator.memory_manager.clear_memory(user_id)
            logger.info(f"Cleared conversation history for session {session_id}")
            return {"status": "success", "message": f"Session {session_id} cleared"}
        
        logger.warning(f"Session {session_id} not found for clearing")
        return {"status": "not_found", "message": f"Session {session_id} not found"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")


@router.post("/rag/knowledge-base/process", response_model=Dict[str, Any], status_code=202)
async def process_knowledge_base(
    request: Request,
    background_tasks: BackgroundTasks,
    domain: Optional[str] = None,
):
    """Process knowledge base files through MCP."""
    try:
        mcp_client = get_mcp_client()
        if not mcp_client:
            raise HTTPException(
                status_code=503, detail="MCP client not initialized")

        result = await mcp_client.invoke_tool("rag.knowledge-base.process", {
            "domain": domain
        })
        return result
    except Exception as e:
        logger.error(f"Error processing knowledge base through MCP: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing knowledge base: {str(e)}")


@router.post("/knowledge-base/upload", response_model=ProcessPDFResponse)
async def upload_pdf_to_knowledge_base(
    file: UploadFile = File(...),
    domain: Optional[str] = None,
) -> ProcessPDFResponse:
    """Upload a PDF file to the knowledge base through MCP."""
    try:
        # Read file content
        content = await file.read()

        # Send file to MCP
        mcp_client = get_mcp_client()
        if not mcp_client:
            raise HTTPException(
                status_code=503, detail="MCP client not initialized")

        result = await mcp_client.invoke_tool("knowledge-base.upload", {
            "filename": file.filename,
            "content": content,
            "domain": domain
        })

        return ProcessPDFResponse(
            status="success",
            message=f"PDF processed successfully: {file.filename}",
            processed_files=result.get("content", {}).get("files", [])
        )
    except Exception as e:
        logger.error(f"Error processing PDF through MCP: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )


@router.post("/entity/create", response_model=AIResponse)
async def create_entity(
    request: AIRequest,
    session_id: Optional[str] = Cookie(None)
) -> AIResponse:
    """Create a new entity through MCP."""
    try:
        # Use session ID if provided
        active_session_id = request.session_id or session_id or str(uuid.uuid4())
        
        mcp_client = get_mcp_client()
        if not mcp_client:
            raise HTTPException(
                status_code=503, detail="MCP client not initialized")

        result = await mcp_client.invoke_tool("entity.create", {
            "prompt": request.prompt,
            "domain": request.domain or "default"
        })

        response_content = {}
        if isinstance(result.get("content"), str):
            try:
                response_content = json.loads(result["content"])
            except:
                response_content = {"response": result.get(
                    "content", "Entity created")}
        else:
            response_content = result.get("content", {})

        return AIResponse(
            response=response_content.get("response", "Entity created"),
            intent=response_content.get("intent", "create"),
            target=response_content.get("target", "unknown"),
            description=response_content.get(
                "description", "Create entity from description"),
            rag_used=response_content.get("rag_used", False),
            cached=response_content.get("cached", False),
            confidence=response_content.get("confidence", 0.9),
            error=response_content.get("error", False),
            error_message=response_content.get("error_message"),
            session_id=active_session_id
        )
    except Exception as e:
        logger.error(f"Error creating entity through MCP: {str(e)}")
        return AIResponse(
            response=f"Error creating entity: {str(e)}",
            intent="create",
            target="unknown",
            description="Create entity from description",
            rag_used=False,
            cached=False,
            confidence=0.0,
            error=True,
            error_message=str(e),
            session_id=request.session_id or session_id
        )

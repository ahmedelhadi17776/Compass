from fastapi import APIRouter, HTTPException, status, Query, File, UploadFile
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging
import os
import shutil
from pathlib import Path
from fastapi import Request, BackgroundTasks
import json

from Backend.ai_services.llm.llm_service import LLMService
from Backend.orchestration.ai_orchestrator import AIOrchestrator
from Backend.app.schemas.message_schemas import UserMessage, AssistantMessage, ConversationHistory
from Backend.core.config import settings
from Backend.mcp.client import MCPClient

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
llm_service = LLMService()
mcp_client = MCPClient(settings.GO_BACKEND_URL)


@router.post("/process", response_model=AIResponse)
async def process_ai_request(
    request: AIRequest,
) -> AIResponse:
    """Process an AI request through MCP."""
    try:
        orchestrator = AIOrchestrator()

        # Process request
        result = await orchestrator.process_request(
            user_input=request.prompt,
            user_id=1,  # Temporary user ID, will be replaced by MCP auth
            domain=request.domain or "default"
        )

        return AIResponse(**result)
    except Exception as e:
        logger.error(f"Error processing AI request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/rag/stats/{domain}")
async def get_rag_stats(
    domain: str,
):
    """Get RAG statistics for a specific domain through MCP."""
    try:
        result = await mcp_client.call_method("rag/stats", {
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
        result = await mcp_client.call_method("rag/update", {
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
        result = await mcp_client.call_method("ai/model/info", {})
        return result
    except Exception as e:
        logger.error(f"Error getting model info through MCP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/knowledge-base/process", response_model=Dict[str, Any], status_code=202)
async def process_knowledge_base(
    request: Request,
    background_tasks: BackgroundTasks,
    domain: Optional[str] = None,
):
    """Process knowledge base files through MCP."""
    try:
        result = await mcp_client.call_method("rag/knowledge-base/process", {
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
        result = await mcp_client.call_method("knowledge-base/upload", {
            "filename": file.filename,
            "content": content,
            "domain": domain
        })

        return ProcessPDFResponse(
            status="success",
            message=f"PDF processed successfully: {file.filename}",
            processed_files=result.get("files", [])
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
) -> AIResponse:
    """Create a new entity through MCP."""
    try:
        result = await mcp_client.call_method("entity/create", {
            "prompt": request.prompt,
            "domain": request.domain or "default"
        })

        return AIResponse(
            response=result.get("response", "Entity created"),
            intent=result.get("intent", "create"),
            target=result.get("target", "unknown"),
            description=result.get(
                "description", "Create entity from description"),
            rag_used=result.get("rag_used", False),
            cached=result.get("cached", False),
            confidence=result.get("confidence", 0.9),
            error=result.get("error", False),
            error_message=result.get("error_message")
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
            error_message=str(e)
        )

from fastapi import FastAPI, Request, HTTPException
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount
from Backend.orchestration.ai_orchestrator import AIOrchestrator
from Backend.core.config import settings
from typing import Dict, Any, Optional, AsyncIterator, Union, AsyncGenerator
from fastapi.responses import StreamingResponse
import logging
import httpx
import os
import json
import sys
import asyncio
from mcp.types import (
    InitializeResult,
    ServerCapabilities,
    Implementation,
    ToolsCapability,
    LoggingCapability
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mcp_server.log')
    ]
)
logger = logging.getLogger(__name__)

# Set Windows-compatible event loop policy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logger.info("Set Windows-compatible event loop policy in server")

# Initialize FastAPI app
app = FastAPI()

# Initialize FastMCP server with explicit file path handling
current_dir = os.path.dirname(os.path.abspath(__file__))
mcp = FastMCP(
    name="compass",
    version="1.0.0",
    instructions="COMPASS AI Service MCP Server"
)

# Create SSE transport instance
sse = SseServerTransport("/mcp/sse")

# Mount the SSE endpoint for MCP
app.router.routes.append(Mount("/mcp/sse", app=sse.handle_post_message))

# Constants
GO_BACKEND_URL = f"http://{settings.api_host}:{settings.api_port}"
HEADERS = {"Content-Type": "application/json"}


@mcp.tool()
async def create_user(user_data: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
    """Create a new user in the system.

    Args:
        user_data: Dictionary containing user information
            - username: str
            - email: str
            - password: str
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{GO_BACKEND_URL}/api/v1/users",
                json=user_data,
                headers=HEADERS
            )
            response.raise_for_status()
            await ctx.info(f"Created user: {user_data['username']}")
            return response.json()
        except Exception as e:
            await ctx.error(f"Failed to create user: {str(e)}")
            raise


@mcp.tool()
async def get_user(user_id: str, ctx: Context) -> Dict[str, Any]:
    """Get user information by ID.

    Args:
        user_id: The ID of the user to retrieve
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GO_BACKEND_URL}/api/v1/users/{user_id}",
                headers=HEADERS
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            await ctx.error(f"Failed to get user {user_id}: {str(e)}")
            raise


@mcp.tool()
async def create_task(task_data: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
    """Create a new task.

    Args:
        task_data: Dictionary containing task information
            - title: str
            - description: str
            - due_date: str (optional)
            - priority: str (optional)
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{GO_BACKEND_URL}/api/v1/tasks",
                json=task_data,
                headers=HEADERS
            )
            response.raise_for_status()
            await ctx.info(f"Created task: {task_data['title']}")
            return response.json()
        except Exception as e:
            await ctx.error(f"Failed to create task: {str(e)}")
            raise


@mcp.tool()
async def get_tasks(user_id: str, ctx: Context) -> Dict[str, Any]:
    """Get all tasks for a user.

    Args:
        user_id: The ID of the user
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GO_BACKEND_URL}/api/v1/tasks",
                params={"user_id": user_id},
                headers=HEADERS
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            await ctx.error(f"Failed to get tasks for user {user_id}: {str(e)}")
            raise


@mcp.tool()
async def create_project(project_data: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
    """Create a new project.

    Args:
        project_data: Dictionary containing project information
            - name: str
            - description: str
            - start_date: str (optional)
            - end_date: str (optional)
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{GO_BACKEND_URL}/api/v1/projects",
                json=project_data,
                headers=HEADERS
            )
            response.raise_for_status()
            await ctx.info(f"Created project: {project_data['name']}")
            return response.json()
        except Exception as e:
            await ctx.error(f"Failed to create project: {str(e)}")
            raise


@mcp.tool("ai.process")
async def process_ai_request(
    ctx: Context,
    prompt: str,
    user_id: str,
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """Process an AI request through MCP."""
    try:
        orchestrator = AIOrchestrator()
        result = await orchestrator.process_request(
            user_input=prompt,
            user_id=int(user_id),
            domain=domain or "default"
        )
        return result
    except Exception as e:
        logger.error(f"Error processing AI request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp.tool("ai.stream")
async def stream_ai_response(
    ctx: Context,
    prompt: str,
    user_id: str,
    domain: Optional[str] = None
) -> AsyncIterator[str]:
    """Stream AI responses through MCP."""
    try:
        orchestrator = AIOrchestrator()
        response = await orchestrator.llm_service.generate_response(
            prompt=prompt,
            context={"user_id": user_id, "domain": domain or "default"},
            stream=True
        )

        if isinstance(response, AsyncGenerator):
            async for chunk in response:
                yield chunk
        elif isinstance(response, dict):
            yield response.get("text", "")
        else:
            yield str(response)
    except Exception as e:
        logger.error(f"Error streaming AI response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Add tools to match REST-style endpoints used in the client
@mcp.tool("ai.model.info")
async def get_model_info(
    ctx: Context,
    name: Optional[str] = None,
    version: Optional[str] = None
) -> Dict[str, Any]:
    """Get model information."""
    try:
        return {
            "model_id": 1,  # Default model ID
            "name": name or "gpt-4",
            "version": version or "1.0",
            "type": "text-generation",
            "provider": "OpenAI",
            "capabilities": {
                "streaming": True,
                "function_calling": True
            }
        }
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise


@mcp.tool("ai.model.create")
async def create_model(
    ctx: Context,
    name: str,
    version: str,
    type: str,
    provider: str,
    status: str
) -> Dict[str, Any]:
    """Create a new model."""
    try:
        return {
            "model_id": 1,
            "name": name,
            "version": version,
            "type": type,
            "provider": provider,
            "status": status,
            "created_at": "2023-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error creating model: {str(e)}")
        raise


@mcp.tool("ai.model.stats.update")
async def update_model_stats(
    ctx: Context,
    model_id: int,
    latency: float,
    success: bool
) -> Dict[str, Any]:
    """Update model usage statistics."""
    try:
        return {
            "model_id": model_id,
            "updated_at": "2023-01-01T00:00:00Z",
            "success": success,
            "latency": latency
        }
    except Exception as e:
        logger.error(f"Error updating model stats: {str(e)}")
        raise


@mcp.tool("ai.log.interaction")
async def log_interaction(
    ctx: Context,
    user_id: str,
    domain: Optional[str],
    input: str,
    output: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Log AI interaction."""
    try:
        logger.info(
            f"Logging interaction for user {user_id} in domain {domain}")
        return {
            "logged": True,
            "timestamp": "2023-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error logging interaction: {str(e)}")
        raise


@mcp.tool("rag.stats")
async def rag_stats(
    ctx: Context,
    domain: str
) -> Dict[str, Any]:
    """Get RAG statistics for a domain."""
    try:
        logger.info(f"Getting RAG statistics for domain: {domain}")
        return {
            "document_count": 10,
            "total_tokens": 50000,
            "last_updated": "2023-01-01T00:00:00Z",
            "domain": domain
        }
    except Exception as e:
        logger.error(f"Error getting RAG stats: {str(e)}")
        raise


@mcp.tool("rag.update")
async def rag_update(
    ctx: Context,
    domain: str,
    content: Dict[str, Any]
) -> Dict[str, Any]:
    """Update RAG knowledge base for a domain."""
    try:
        logger.info(f"Updating RAG knowledge base for domain: {domain}")
        logger.info(f"Content size: {len(str(content))} characters")
        return {
            "updated": True,
            "timestamp": "2023-01-01T00:00:00Z",
            "domain": domain,
            "document_count": 1
        }
    except Exception as e:
        logger.error(f"Error updating RAG knowledge base: {str(e)}")
        raise


@mcp.tool("rag.knowledge-base.process")
async def process_knowledge_base(
    ctx: Context,
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """Process knowledge base files."""
    try:
        logger.info(
            f"Processing knowledge base for domain: {domain or 'default'}")
        return {
            "status": "processing",
            "job_id": "123456",
            "timestamp": "2023-01-01T00:00:00Z",
            "domain": domain or "default"
        }
    except Exception as e:
        logger.error(f"Error processing knowledge base: {str(e)}")
        raise


@mcp.tool("knowledge-base.upload")
async def upload_to_knowledge_base(
    ctx: Context,
    filename: str,
    content: bytes,
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """Upload a file to knowledge base."""
    try:
        logger.info(
            f"Uploading file {filename} to knowledge base for domain: {domain or 'default'}")
        logger.info(f"Content size: {len(content)} bytes")
        return {
            "status": "success",
            "message": f"File {filename} uploaded successfully",
            "files": [
                {
                    "filename": filename,
                    "size": len(content),
                    "upload_time": "2023-01-01T00:00:00Z"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error uploading to knowledge base: {str(e)}")
        raise


@mcp.tool("entity.create")
async def create_entity(
    ctx: Context,
    prompt: str,
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """Create an entity from a prompt."""
    try:
        logger.info(
            f"Creating entity from prompt in domain: {domain or 'default'}")
        return {
            "entity_id": "123456",
            "response": f"Created entity from: {prompt[:20]}...",
            "intent": "create",
            "target": domain or "default",
            "description": "Entity created from description",
            "rag_used": False,
            "cached": False,
            "confidence": 0.9
        }
    except Exception as e:
        logger.error(f"Error creating entity: {str(e)}")
        raise


@mcp.tool("user.getContext")
async def get_user_context(
    ctx: Context,
    user_id: str,
    domain: str
) -> Dict[str, Any]:
    """Get user context data."""
    try:
        logger.info(f"Getting context for user {user_id} in domain {domain}")
        return {
            "user_id": user_id,
            "domain": domain,
            "preferences": {
                "language": "en",
                "theme": "light"
            },
            "history": []
        }
    except Exception as e:
        logger.error(f"Error getting user context: {str(e)}")
        raise


@mcp.tool("user.getInfo")
async def get_user_info(
    ctx: Context,
    user_id: str
) -> Dict[str, Any]:
    """Get user information."""
    try:
        logger.info(f"Getting info for user {user_id}")
        return {
            "user_id": user_id,
            "name": "Test User",
            "email": "test@example.com",
            "created_at": "2023-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise


def setup_mcp_server(app: Optional[FastAPI] = None):
    """Setup and return the MCP server instance"""
    if app is not None:
        # Mount the SSE endpoint for MCP on the main app
        app.router.routes.append(
            Mount("/mcp/sse", app=sse.handle_post_message))
    return mcp


async def run_server():
    """Run the MCP server with stdio transport."""
    try:
        logger.info("Starting MCP server with stdio transport")
        
        if sys.platform == "win32":
            # Windows-specific setup
            # Ensure stdout is in binary mode on Windows
            import msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            logger.info("Set stdin/stdout to binary mode for Windows")
            
            # Use a custom loop explicitly for Windows
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(mcp.run_stdio_async())
            finally:
                loop.close()
        else:
            # Non-Windows platforms can use the standard approach
            await mcp.run_stdio_async()
    except Exception as e:
        logger.error(f"Error running MCP server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run the server using stdio transport
    logger.info("Initializing MCP server")
    if sys.platform == "win32":
        # Windows requires special handling for asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logger.info("Set Windows-compatible event loop policy")
    asyncio.run(run_server())

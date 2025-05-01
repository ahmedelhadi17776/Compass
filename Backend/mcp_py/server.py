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

# Initialize FastAPI app
app = FastAPI()

# Initialize FastMCP server
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
        await mcp.run_stdio_async()
    except Exception as e:
        logger.error(f"Error running MCP server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run the server using stdio transport
    logger.info("Initializing MCP server")
    asyncio.run(run_server())

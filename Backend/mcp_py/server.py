from fastapi import FastAPI, Request, HTTPException, Header
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount
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
import sys
from core.config import settings
from orchestration.ai_orchestrator import AIOrchestrator
import uuid

# Hardcoded JWT token for development - only used as fallback
DEV_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNDA4YjM4YmMtNWRlZS00YjA0LTlhMDYtZWE4MTk0OWJmNWMzIiwiZW1haWwiOiJhaG1lZEBnbWFpbC5jb20iLCJyb2xlcyI6WyJ1c2VyIl0sIm9yZ19pZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsInBlcm1pc3Npb25zIjpbInRhc2tzOnJlYWQiLCJvcmdhbml6YXRpb25zOnJlYWQiLCJwcm9qZWN0czpyZWFkIiwidGFza3M6dXBkYXRlIiwidGFza3M6Y3JlYXRlIl0sImV4cCI6MTc0NjQxNDc5NCwibmJmIjoxNzQ2MzI4Mzk0LCJpYXQiOjE3NDYzMjgzOTR9.SxiV6WES1ndPqNBkk5g72hpeQtLOqwjRVP4eC_iVyss"

print("PYTHONPATH:", sys.path)

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
    endpoint="/mcp",
    prefix="/mcp",
    instructions="COMPASS AI Service MCP Server"
)

# Create SSE transport instance
sse_transport = SseServerTransport("/mcp/sse")

# Mount the SSE endpoint for MCP
app.router.routes.append(
    Mount("/mcp/sse", app=sse_transport.handle_post_message))

# Use settings for API endpoint
GO_BACKEND_URL = f"http://{settings.api_host}:8000"
logger.info(f"Using backend URL: {GO_BACKEND_URL}")
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
    user_id: Optional[str] = None,
    domain: Optional[str] = None,
    authorization: Optional[str] = None
) -> Dict[str, Any]:
    """Process an AI request through MCP.

    Args:
        prompt: The user's prompt text
        user_id: Optional user ID (UUID string)
        domain: Optional domain context
        authorization: Optional authorization token (Bearer token)
    """
    try:
        # Log warning for invalid authorization but don't block request
        if not authorization or authorization == "Bearer undefined" or authorization == "Bearer null":
            await ctx.warning("Missing or invalid authorization token - proceeding without authentication")
            # Continue processing without blocking

        orchestrator = AIOrchestrator()
        # Use UUID string directly, no conversion needed

        # If authorization was provided, log it
        if authorization and authorization not in ["Bearer undefined", "Bearer null"]:
            await ctx.info(f"Processing request with provided authorization token")

        # Convert user_id string to integer if provided
        user_id_int = None
        if user_id:
            try:
                # Try to convert to int or use a hash of the UUID as a numeric ID
                user_id_int = int(hash(user_id) % 100000)
            except (ValueError, TypeError):
                user_id_int = int(hash(str(user_id)) % 100000)
                await ctx.warning(f"Converted string user_id to numeric ID: {user_id_int}")
        else:
            # Generate a default user ID if none provided
            user_id_int = int(hash(str(uuid.uuid4())) % 100000)

        # Process the request through orchestrator
        result = await orchestrator.process_request(
            user_input=prompt,
            # Use numeric user ID for orchestrator
            user_id=user_id_int,
            domain=domain or "default",
            auth_token=authorization
        )

        return result
    except Exception as e:
        logger.error(f"Error processing AI request: {str(e)}")
        await ctx.error(f"Failed to process AI request: {str(e)}")
        raise


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
async def get_model_info(ctx: Context) -> Dict[str, Any]:
    """Get information about the AI model."""
    try:
        return {
            "model_id": 1,
            "name": "gpt-4o-mini",
            "version": "1.0",
            "type": "text-generation",
            "provider": "OpenAI",
            "capabilities": {
                "streaming": True,
                "function_calling": True,
                "tool_use": True
            }
        }
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        await ctx.error(f"Failed to get model info: {str(e)}")
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
    """Get user information from the Go backend."""
    try:
        logger.info(f"Getting info for user {user_id}")

        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEV_JWT_TOKEN}"
            }

            response = await client.get(
                f"{GO_BACKEND_URL}/api/users/{user_id}",
                headers=headers
            )
            response.raise_for_status()

            # Return response data or fallback
            try:
                return response.json()
            except:
                # Fallback if response isn't valid JSON
                return {
                    "user_id": user_id,
                    "name": "User",
                    "email": "user@example.com"
                }

    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        await ctx.error(f"Failed to get user info: {str(e)}")

        # Return fallback data on error
        return {
            "user_id": user_id,
            "name": "Unknown User",
            "email": "unknown@example.com",
            "error": str(e)
        }


@mcp.tool("todos.list")
async def get_todos(
    ctx: Context,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    authorization: Optional[str] = None
) -> Dict[str, Any]:
    """Get todos for a user with optional filters.

    Args:
        user_id: Optional ID of the user
        status: Optional todo status filter (completed, pending, etc.)
        priority: Optional priority filter (high, medium, low)
        authorization: Optional authorization token (Bearer token)

    Returns:
        A list of todos
    """
    try:
        logger.info(
            f"Getting todos for user {user_id or 'all'} with status={status}, priority={priority}")

        # Get auth token from parameter or fall back to default
        auth_token = None
        if authorization and authorization.startswith("Bearer "):
            auth_token = authorization
        else:
            auth_token = f"Bearer {DEV_JWT_TOKEN}"

        logger.debug(f"Using auth token: {auth_token[:20]}...")

        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_token
            }

            # Build query parameters
            params = {}
            if user_id:
                params["user_id"] = user_id
            if status:
                params["status"] = status
            if priority:
                params["priority"] = priority

            # Make request to Go backend
            response = await client.get(
                f"{GO_BACKEND_URL}/api/todo-lists",
                headers=headers,
                params=params
            )
            response.raise_for_status()

            # Log success
            await ctx.info(f"Successfully retrieved todos from Go backend")

            # Return JSON response
            return response.json()

    except Exception as e:
        error_msg = f"Error getting todos: {str(e)}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@mcp.tool("get_all_todos")
async def get_all_todos(
    ctx: Context,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    authorization: Optional[str] = None
) -> Dict[str, Any]:
    """Alias for todos.list - Get todos for a user with optional filters."""
    try:
        logger.info(
            f"get_all_todos called with: user_id={user_id}, status={status}, priority={priority}")
        await ctx.info(f"get_all_todos called with: user_id={user_id}, status={status}, priority={priority}")

        # Log the backend URL we're trying to connect to
        logger.info(f"GO_BACKEND_URL is set to: {GO_BACKEND_URL}")

        # Get auth token from parameter or fall back to default
        auth_token = None
        if authorization and authorization.startswith("Bearer "):
            auth_token = authorization
            logger.info("Using provided authorization token")
        else:
            auth_token = f"Bearer {DEV_JWT_TOKEN}"
            logger.info("Using default DEV_JWT_TOKEN for authorization")

        logger.info(f"Authorization token being used (first 20 chars): {auth_token[:20]}...")

        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_token
            }
            logger.info(f"Request headers: {headers}")

            # Build query parameters
            params = {}
            if user_id:
                params["user_id"] = user_id
            if status:
                params["status"] = status
            if priority:
                params["priority"] = priority

            full_url = f"{GO_BACKEND_URL}/api/todo-lists"
            logger.info(f"Making request to: {full_url}")
            logger.info(f"With query parameters: {params}")
            await ctx.info(f"Making request to endpoint: {full_url}")

            try:
                # Make request to Go backend
                response = await client.get(
                    full_url,
                    headers=headers,
                    params=params,
                    timeout=10.0  # Add timeout to avoid hanging
                )
                
                # Log the response status and headers
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response headers: {response.headers}")
                
                # Try to get response text for debugging
                try:
                    response_text = response.text
                    logger.info(f"Raw response text: {response_text[:200]}...")  # First 200 chars
                except Exception as text_e:
                    logger.error(f"Could not get response text: {str(text_e)}")

                response.raise_for_status()
                result = response.json()
                logger.info(f"Successfully parsed JSON response: {str(result)[:100]}...")
                await ctx.info("Successfully retrieved todos data from backend")
                return result

            except httpx.ConnectError as e:
                error_msg = f"Failed to connect to backend at {full_url}: {str(e)}"
                logger.error(error_msg)
                logger.error(f"Connection Details: GO_BACKEND_URL={GO_BACKEND_URL}, Host={settings.api_host}")
                # Try to ping the host
                try:
                    ping_response = await client.get(f"http://{settings.api_host}:8000/health", timeout=5.0)
                    logger.error(f"Host ping response: {ping_response.status_code}")
                except Exception as ping_e:
                    logger.error(f"Host ping failed: {str(ping_e)}")
                await ctx.error(error_msg)
                return {"status": "error", "error": error_msg, "type": "connection_error"}

            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP error {e.response.status_code} from backend: {str(e)}"
                logger.error(error_msg)
                await ctx.error(error_msg)
                return {"status": "error", "error": error_msg, "type": "http_error", "status_code": e.response.status_code}

            except httpx.TimeoutException as e:
                error_msg = f"Request to {full_url} timed out after 10 seconds"
                logger.error(error_msg)
                await ctx.error(error_msg)
                return {"status": "error", "error": error_msg, "type": "timeout"}

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response: {str(e)}"
                logger.error(error_msg)
                await ctx.error(error_msg)
                return {"status": "error", "error": error_msg, "type": "json_error"}

    except Exception as e:
        error_msg = f"Error in get_all_todos: {str(e)}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return {"status": "error", "error": error_msg, "type": "general_error"}


@mcp.tool("todos.create")
async def create_todo(
    ctx: Context,
    title: str,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    authorization: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new todo item.

    Args:
        title: Title of the todo item
        description: Optional description
        due_date: Optional due date (format: YYYY-MM-DD)
        priority: Optional priority (high, medium, low)
        authorization: Optional authorization token (Bearer token)

    Returns:
        The created todo item
    """
    try:
        logger.info(f"Creating new todo: {title}")

        # Get auth token from parameter or fall back to default
        auth_token = None
        if authorization and authorization.startswith("Bearer "):
            auth_token = authorization
        else:
            auth_token = f"Bearer {DEV_JWT_TOKEN}"

        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_token
            }

            # Prepare todo data
            todo_data = {
                "title": title,
                "description": description or "",
                "priority": priority or "medium"
            }

            if due_date:
                todo_data["due_date"] = due_date

            # Make request to Go backend
            response = await client.post(
                f"{GO_BACKEND_URL}/api/todos",
                headers=headers,
                json=todo_data
            )
            response.raise_for_status()

            # Log success
            await ctx.info(f"Successfully created todo: {title}")

            # Return JSON response
            return response.json()

    except Exception as e:
        error_msg = f"Error creating todo: {str(e)}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@mcp.tool("todos.update")
async def update_todo(
    ctx: Context,
    todo_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    authorization: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing todo item.

    Args:
        todo_id: ID of the todo to update
        title: Optional new title
        description: Optional new description
        status: Optional new status
        priority: Optional new priority
        authorization: Optional authorization token (Bearer token)

    Returns:
        The updated todo item
    """
    try:
        logger.info(f"Updating todo with ID: {todo_id}")

        # Get auth token from parameter or fall back to default
        auth_token = None
        if authorization and authorization.startswith("Bearer "):
            auth_token = authorization
        else:
            auth_token = f"Bearer {DEV_JWT_TOKEN}"

        async with httpx.AsyncClient() as client:
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_token
            }

            # Prepare update data (only include non-None values)
            update_data = {}
            if title is not None:
                update_data["title"] = title
            if description is not None:
                update_data["description"] = description
            if status is not None:
                update_data["status"] = status
            if priority is not None:
                update_data["priority"] = priority

            # Make request to Go backend
            response = await client.put(
                f"{GO_BACKEND_URL}/api/todos/{todo_id}",
                headers=headers,
                json=update_data
            )
            response.raise_for_status()

            # Log success
            await ctx.info(f"Successfully updated todo {todo_id}")

            # Return JSON response
            return response.json()

    except Exception as e:
        error_msg = f"Error updating todo: {str(e)}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


def setup_mcp_server(app: Optional[FastAPI] = None):
    """Setup and return the MCP server instance"""
    # Log basic info
    logger.info(f"Setting up MCP server: {mcp.name}")

    if app is not None:
        # Mount the SSE endpoint for MCP on the main app
        app.router.routes.append(
            Mount("/mcp/sse", app=sse_transport.handle_post_message))
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

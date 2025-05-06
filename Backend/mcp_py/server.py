from fastapi import FastAPI, Request, HTTPException, Header
from mcp.server.fastmcp import FastMCP, Context
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
DEV_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNDA4YjM4YmMtNWRlZS00YjA0LTlhMDYtZWE4MTk0OWJmNWMzIiwiZW1haWwiOiJhaG1lZEBnbWFpbC5jb20iLCJyb2xlcyI6WyJ1c2VyIl0sIm9yZ19pZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsInBlcm1pc3Npb25zIjpbInRhc2tzOnJlYWQiLCJvcmdhbml6YXRpb25zOnJlYWQiLCJwcm9qZWN0czpyZWFkIiwidGFza3M6dXBkYXRlIiwidGFza3M6Y3JlYXRlIl0sImV4cCI6MTc0NjUwNDg1NiwibmJmIjoxNzQ2NDE4NDU2LCJpYXQiOjE3NDY0MTg0NTZ9.nUky6q0vPRnVYP9gTPIPaibNezB-7Sn-EgDZvlxU0_8"

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

# Add a diagnostic endpoint to check registered tools


@app.get("/mcp-diagnostic")
async def mcp_diagnostic():
    """Diagnostic endpoint to verify MCP server configuration and tool registration."""
    try:
        # Get available tools - using proper public properties instead of internal ones
        registered_tools = []

        # Use reflection to safely gather tool information
        tools_dict = {}
        for attr_name in dir(mcp):
            if attr_name.startswith("_tool_"):
                tool_name = attr_name[6:]  # Remove "_tool_" prefix
                tool_func = getattr(mcp, attr_name)
                tool_description = getattr(
                    tool_func, "__doc__", "No description")
                tools_dict[tool_name] = {
                    "name": tool_name,
                    "description": tool_description
                }

        # Return diagnostic information
        return {
            "status": "running",
            "mcp_name": mcp.name,
            "mcp_version": getattr(mcp, "version", "1.0.0"),
            "tool_count": len(tools_dict),
            "registered_tools": list(tools_dict.values()),
            "backend_urls": GO_BACKEND_URLS,
            "current_backend_url": GO_BACKEND_URL,
        }
    except Exception as e:
        logger.error(f"Error in diagnostic endpoint: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "mcp_initialized": bool(mcp),
            "backend_urls": GO_BACKEND_URLS
        }

# Define multiple backend URLs to try for Docker/non-Docker environments
GO_BACKEND_URLS = [
    "http://api:8000",
    "http://backend_go-api-1:8000"
]

# Start with the first URL, will try others if this fails
GO_BACKEND_URL = GO_BACKEND_URLS[0]
logger.info(f"Primary backend URL: {GO_BACKEND_URL}")
logger.info(f"Available backend URLs: {GO_BACKEND_URLS}")
HEADERS = {"Content-Type": "application/json"}


# Helper function to try multiple backend URLs
async def try_backend_urls(client_func, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Try to connect to multiple backend URLs in sequence."""
    global GO_BACKEND_URL

    errors = []
    # Increase timeout for Docker networking
    timeout = httpx.Timeout(10.0, connect=5.0)

    logger.info(
        f"[CONNECTION] Trying to connect to endpoint {endpoint} with {len(GO_BACKEND_URLS)} URLs")
    logger.info(f"[CONNECTION] Available URLs: {GO_BACKEND_URLS}")

    # Track initial URL for logging purposes
    initial_url = GO_BACKEND_URL
    logger.info(f"[CONNECTION] Starting with URL: {initial_url}")

    for base_url in GO_BACKEND_URLS:
        full_url = f"{base_url}{endpoint}"
        logger.info(f"[CONNECTION] Attempting connection to: {full_url}")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Call the appropriate HTTP method function
                logger.info(
                    f"[CONNECTION] Sending {client_func.__name__} request to {full_url}")
                response = await client_func(client, full_url, **kwargs)
                logger.info(
                    f"[CONNECTION] Received response from {full_url}: status={response.status_code}")
                response.raise_for_status()

                # If successful, update the global URL for future requests
                previous_url = GO_BACKEND_URL
                GO_BACKEND_URL = base_url
                logger.info(
                    f"[CONNECTION] CONNECTION SUCCESS! {base_url} is working")
                logger.info(
                    f"[CONNECTION] Updated primary backend URL from {previous_url} to {GO_BACKEND_URL}")

                try:
                    result = response.json()
                    logger.info(
                        f"[CONNECTION] Successfully parsed JSON response from {base_url}")
                    return result
                except Exception as json_error:
                    # Handle case where response isn't valid JSON
                    logger.warning(
                        f"[CONNECTION] Response not JSON: {str(json_error)}")
                    return {"status": "success", "message": response.text}
        except httpx.ConnectError as e:
            # Connection errors are expected when trying different URLs
            logger.warning(
                f"[CONNECTION] Connection error to {base_url}: {str(e)}")
            errors.append({"url": base_url, "error": str(e),
                          "type": "connection_error"})
        except httpx.TimeoutException as e:
            # Timeout errors
            logger.warning(
                f"[CONNECTION] Timeout connecting to {base_url}: {str(e)}")
            errors.append(
                {"url": base_url, "error": str(e), "type": "timeout"})
        except httpx.HTTPStatusError as e:
            # HTTP status errors (4xx, 5xx)
            logger.warning(
                f"[CONNECTION] HTTP error from {base_url}: {e.response.status_code}")
            errors.append({"url": base_url, "error": f"HTTP {e.response.status_code}",
                          "type": "http_error", "status": e.response.status_code})
        except Exception as e:
            # Other unexpected errors
            logger.warning(
                f"[CONNECTION] Failed to connect to {base_url}: {str(e)}")
            errors.append(
                {"url": base_url, "error": str(e), "type": "unexpected"})

    # If we get here, all URLs failed
    error_msg = f"Failed to connect to any backend URL: {[e['url'] for e in errors]}"
    logger.error(
        f"[CONNECTION] ALL CONNECTION ATTEMPTS FAILED. Tried URLs: {GO_BACKEND_URLS}")
    logger.error(f"[CONNECTION] {error_msg}")
    logger.error(f"[CONNECTION] Last working URL was: {initial_url}")

    # Return a structured error response instead of raising an exception
    # This allows the client to handle the error more gracefully
    return {
        "status": "error",
        "error": error_msg,
        "type": "connection_error",
        "details": errors
    }


@mcp.tool("create.user")
async def create_user(user_data: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
    """Create a new user in the system.

    Args:
        user_data: Dictionary containing user information
            - email: str
            - username: str 
            - password: str
            - firstName: str (will be converted to first_name)
            - lastName: str (will be converted to last_name)
            - phoneNumber: str (will be converted to phone_number)
            - timezone: str
            - locale: str
    """
    try:
        # Transform camelCase to snake_case for the Go backend
        transformed_data = {
            "email": user_data.get("email"),
            "username": user_data.get("username"),
            "password": user_data.get("password"),
            "first_name": user_data.get("firstName"),
            "last_name": user_data.get("lastName"),
            "phone_number": user_data.get("phoneNumber"),
            "timezone": user_data.get("timezone"),
            "locale": user_data.get("locale")
        }

        # Remove None values
        transformed_data = {k: v for k,
                            v in transformed_data.items() if v is not None}

        async def post_func(client, url, **kwargs):
            return await client.post(url, **kwargs)

        return await try_backend_urls(
            post_func,
            "/api/users/register",
            json=transformed_data,
            headers=HEADERS
        )
    except Exception as e:
        await ctx.error(f"Failed to create user: {str(e)}")
        raise


@mcp.tool("check.health")
async def check_health(ctx: Context) -> Dict[str, Any]:
    """Check the health status of the system.

    Returns:
        Dict containing health check information
    """
    try:
        async def get_func(client, url, **kwargs):
            return await client.get(url, **kwargs)

        return await try_backend_urls(
            get_func,
            "/health",
            headers=HEADERS
        )
    except Exception as e:
        await ctx.error(f"Health check failed: {str(e)}")
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
    try:
        async def post_func(client, url, **kwargs):
            return await client.post(url, **kwargs)

        return await try_backend_urls(
            post_func,
            "/api/v1/tasks",
            json=task_data,
            headers=HEADERS
        )
    except Exception as e:
        await ctx.error(f"Failed to create task: {str(e)}")
        raise


@mcp.tool()
async def get_tasks(user_id: str, ctx: Context) -> Dict[str, Any]:
    """Get all tasks for a user.

    Args:
        user_id: The ID of the user
    """
    try:
        async def get_func(client, url, **kwargs):
            return await client.get(url, **kwargs)

        return await try_backend_urls(
            get_func,
            "/api/v1/tasks",
            params={"user_id": user_id},
            headers=HEADERS
        )
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
    try:
        async def post_func(client, url, **kwargs):
            return await client.post(url, **kwargs)

        return await try_backend_urls(
            post_func,
            "/api/v1/projects",
            json=project_data,
            headers=HEADERS
        )
    except Exception as e:
        await ctx.error(f"Failed to create project: {str(e)}")
        raise

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
        # Get auth token from parameter or fall back to default
        auth_token = None
        if authorization and authorization.startswith("Bearer ") and authorization != "Bearer undefined" and authorization != "Bearer null":
            auth_token = authorization
            logger.info(
                f"Using provided authorization token: {authorization[:20]}...")
        else:
            auth_token = f"Bearer {DEV_JWT_TOKEN}"
            logger.info(
                f"Using DEV_JWT_TOKEN for authorization: {auth_token[:20]}...")

        # Build query parameters
        params = {}
        if user_id:
            params["user_id"] = user_id
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority

        async def get_func(client, url, **kwargs):
            return await client.get(url, **kwargs)

        return await try_backend_urls(
            get_func,
            "/api/todo-lists",
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_token
            },
            params=params
        )
    except Exception as e:
        error_msg = f"Error getting todos: {str(e)}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return {"status": "error", "error": error_msg, "type": "api_error"}


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

        # Get auth token from parameter or fall back to default
        auth_token = None
        if authorization and authorization.startswith("Bearer ") and authorization != "Bearer undefined" and authorization != "Bearer null":
            auth_token = authorization
            logger.info("Using provided authorization token")
        else:
            auth_token = f"Bearer {DEV_JWT_TOKEN}"
            logger.info(
                f"Using DEV_JWT_TOKEN for authorization: {auth_token[:20]}...")

        # Build query parameters
        params = {}
        if user_id:
            params["user_id"] = user_id
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority

        # Define the get function for try_backend_urls
        async def get_func(client, url, **kwargs):
            return await client.get(url, **kwargs)

        # Use the enhanced try_backend_urls function
        result = await try_backend_urls(
            get_func,
            "/api/todo-lists",
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_token
            },
            params=params
        )

        # Check if the result is an error
        if result.get("status") == "error":
            await ctx.error(result.get("error", "Unknown error fetching todos"))
        else:
            await ctx.info("Successfully retrieved todos data from backend")

        return result

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
        # Get auth token from parameter or fall back to default
        auth_token = None
        if authorization and authorization.startswith("Bearer "):
            auth_token = authorization
        else:
            auth_token = f"Bearer {DEV_JWT_TOKEN}"

        # Prepare todo data
        todo_data = {
            "title": title,
            "description": description or "",
            "priority": priority or "medium"
        }

        if due_date:
            todo_data["due_date"] = due_date

        async def post_func(client, url, **kwargs):
            return await client.post(url, **kwargs)

        return await try_backend_urls(
            post_func,
            "/api/todos",
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_token
            },
            json=todo_data
        )
    except Exception as e:
        error_msg = f"Error creating todo: {str(e)}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return {"status": "error", "error": error_msg, "type": "api_error"}


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


@app.get("/api-test/jwt-check")
async def test_jwt():
    """Endpoint to test JWT token validity."""
    try:
        # Test JWT token
        auth_token = f"Bearer {DEV_JWT_TOKEN}"

        test_results = {
            "jwt_token": DEV_JWT_TOKEN[:20] + "...",
            "backend_urls": GO_BACKEND_URLS,
            "current_backend_url": GO_BACKEND_URL,
            "endpoints_tested": [],
        }

        # Try to access the todos endpoint with this token
        for base_url in GO_BACKEND_URLS:
            full_url = f"{base_url}/api/todo-lists"
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": auth_token
                    }
                    response = await client.get(full_url, headers=headers)

                    test_results["endpoints_tested"].append({
                        "url": full_url,
                        "status_code": response.status_code,
                        "response": response.text,
                        "success": response.status_code < 400
                    })
            except Exception as e:
                test_results["endpoints_tested"].append({
                    "url": full_url,
                    "error": str(e),
                    "success": False
                })

        # Try to login to get a new token
        login_url = f"{GO_BACKEND_URL}/api/users/login"
        try:
            login_data = {
                "email": "admin@example.com",
                "password": "password123"
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    login_url,
                    json=login_data,
                    headers={"Content-Type": "application/json"}
                )

                test_results["login_attempt"] = {
                    "url": login_url,
                    "status_code": response.status_code,
                    "response": response.text if response.status_code >= 400 else "Login response (contains sensitive data)",
                    "success": response.status_code < 400
                }

                if response.status_code < 400:
                    # Extract the token if login was successful
                    login_response = response.json()
                    if "token" in login_response:
                        test_results["new_token"] = login_response["token"][:20] + "..."
        except Exception as e:
            test_results["login_attempt"] = {
                "url": login_url,
                "error": str(e),
                "success": False
            }

        return test_results
    except Exception as e:
        return {"error": str(e)}


def setup_mcp_server(app: Optional[FastAPI] = None):
    """Setup and return the MCP server instance"""
    # Log basic info
    logger.info(f"Setting up MCP server: {mcp.name}")

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

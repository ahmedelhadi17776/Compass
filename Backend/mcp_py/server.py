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
    "http://localhost:8000",
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


@mcp.tool("get_items")
async def get_items(
    ctx: Context,
    item_type: str,  # "todos" or "habits"
    status: Optional[str] = None,
    priority: Optional[str] = None,
    authorization: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    user_id: Optional[str] = None  # Moved to end to de-emphasize
) -> Dict[str, Any]:
    """Get items (todos or habits) with optional filters.

    Args:
        item_type: Type of items to retrieve ("todos" or "habits")
        status: Optional status to filter by
        priority: Optional priority to filter by
        authorization: Optional authorization token (Bearer token)
        page: Optional page number for pagination
        page_size: Optional page size for pagination
        user_id: Optional user ID to filter by (not required - will use token's user)

    Returns:
        The list of items matching the filters
    """
    try:
        logger.info(
            f"get_items called with: type={item_type}, status={status}, priority={priority}")
        await ctx.info(f"get_items called with: type={item_type}, status={status}, priority={priority}")

        # Validate item type
        if item_type not in ["todos", "habits"]:
            error_msg = f"Invalid item type: {item_type}. Must be 'todos' or 'habits'"
            logger.error(error_msg)
            return {"status": "error", "error": error_msg, "type": "validation_error"}

        # Get auth token from parameter or fall back to default
        auth_token = None
        if authorization and authorization.startswith("Bearer ") and authorization != "Bearer undefined" and authorization != "Bearer null":
            auth_token = authorization
            logger.info("Using provided authorization token")
        else:
            auth_token = f"Bearer {DEV_JWT_TOKEN}"
            logger.info(
                f"Using DEV_JWT_TOKEN for authorization: {auth_token[:20]}...")

        # Build query parameters - only include if provided
        params = {}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if user_id:  # Only include user_id if explicitly provided
            params["user_id"] = user_id

        # Define the get function for try_backend_urls
        async def get_func(client, url, **kwargs):
            return await client.get(url, **kwargs)

        # Determine endpoint based on item type
        endpoint = "/api/todo-lists" if item_type == "todos" else "/api/habits"

        # Use the enhanced try_backend_urls function
        result = await try_backend_urls(
            get_func,
            endpoint,
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_token
            },
            params=params
        )

        # Check if the result is an error
        if result.get("status") == "error":
            await ctx.error(result.get("error", f"Unknown error fetching {item_type}"))
        else:
            await ctx.info(f"Successfully retrieved {item_type} data from backend")

        return result

    except Exception as e:
        error_msg = f"Error in get_items: {str(e)}"
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
    authorization: Optional[str] = None,
    user_id: Optional[str] = None,
    list_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new todo item.

    Args:
        title: Title of the todo item
        description: Optional description
        due_date: Optional due date (format: YYYY-MM-DD)
        priority: Optional priority (high, medium, low)
        authorization: Optional authorization token (Bearer token)
        user_id: Optional user ID (will be extracted from token if not provided)
        list_id: Optional list ID for the todo

    Returns:
        The created todo item
    """
    try:
        # Get auth token from parameter or fall back to default
        auth_token = None
        if authorization and authorization.startswith("Bearer ") and authorization != "Bearer undefined" and authorization != "Bearer null":
            auth_token = authorization
            logger.info("Using provided authorization token")
        else:
            auth_token = f"Bearer {DEV_JWT_TOKEN}"
            logger.info(
                f"Using DEV_JWT_TOKEN for authorization: {auth_token[:20]}...")

        # Prepare todo data matching the Go backend's expected format
        todo_data = {
            "title": title,
            "description": description or "",
            "priority": priority or "medium",
            "status": "pending",
            "is_completed": False,
            "is_recurring": False,
            "due_date": due_date,
            "reminder_time": None,
            "recurrence_pattern": {},
            "tags": {},
            "checklist": {"items": []},
            "linked_task_id": None,
            "linked_calendar_event_id": None,
            "user_id": user_id,  # This will be required
            "list_id": list_id   # This will be required
        }

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


@mcp.tool("habits.create")
async def create_habit(
    ctx: Context,
    title: str,
    description: Optional[str] = None,
    start_day: Optional[str] = None,
    end_day: Optional[str] = None,
    authorization: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new habit.

    Args:
        title: Title of the habit
        description: Optional description
        start_day: Optional start date (format: YYYY-MM-DD)
        end_day: Optional end date (format: YYYY-MM-DD) 
        authorization: Optional authorization token (Bearer token)
        user_id: Optional user ID (will be extracted from token if not provided)

    Returns:
        The created habit
    """
    try:
        # Get auth token from parameter or fall back to default
        auth_token = None
        if authorization and authorization.startswith("Bearer ") and authorization != "Bearer undefined" and authorization != "Bearer null":
            auth_token = authorization
            logger.info("Using provided authorization token")
        else:
            auth_token = f"Bearer {DEV_JWT_TOKEN}"
            logger.info(
                f"Using DEV_JWT_TOKEN for authorization: {auth_token[:20]}...")

        # Prepare habit data matching the Go backend's expected format
        habit_data = {
            "title": title,
            "description": description or "",
            "start_day": start_day,
            "end_day": end_day,
            "user_id": user_id
        }

        async def post_func(client, url, **kwargs):
            return await client.post(url, **kwargs)

        return await try_backend_urls(
            post_func,
            "/api/habits",
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_token
            },
            json=habit_data
        )
    except Exception as e:
        error_msg = f"Error creating habit: {str(e)}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return {"status": "error", "error": error_msg, "type": "api_error"}

@mcp.tool("todos.smartUpdate")
async def smart_update_todo(
    ctx: Context,
    edit_request: str,
    authorization: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Intelligently update a todo item based on the user's description.

    Args:
        edit_request: User's request describing what to edit (e.g., "change the due date of my shopping task to tomorrow")
        authorization: Optional authorization token (Bearer token)
        user_id: Optional user ID (will be extracted from token if not provided)

    Returns:
        The updated todo item
    """
    try:
        # Log the request
        logger.info(f"Smart update request: '{edit_request}'")
        await ctx.info(f"Processing todo update request: '{edit_request}'")

        # Get auth token from parameter or fall back to default
        auth_token = None
        if authorization and authorization.startswith("Bearer ") and authorization != "Bearer undefined" and authorization != "Bearer null":
            auth_token = authorization
            logger.info("Using provided authorization token")
        else:
            auth_token = f"Bearer {DEV_JWT_TOKEN}"
            logger.info(f"Using DEV_JWT_TOKEN for authorization: {auth_token[:20]}...")

        # Step 1: Fetch todos using get_items tool
        logger.info(f"Fetching todos from /api/todo-lists endpoint")
        
        # Define the get function for try_backend_urls
        async def get_func(client, url, **kwargs):
            return await client.get(url, **kwargs)
        
        # Use the same headers as get_items
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth_token
        }

        todos_result = await try_backend_urls(
            get_func,
            "/api/todo-lists",
            headers=headers
        )
        
        if todos_result.get("status") == "error":
            error_msg = todos_result.get("error", "Failed to fetch todos")
            logger.error(f"Failed to fetch todos: {error_msg}")
            await ctx.error(f"Failed to fetch todos: {error_msg}")
            return {"status": "error", "error": error_msg}
            
        # Log the todos we received for debugging
        logger.info(f"Received todos data structure: {type(todos_result)}")
        if "data" in todos_result:
            logger.info(f"Todos data contains 'data' field: {type(todos_result['data'])}")

        # Depending on the structure, we might need to adjust
        todos_context = todos_result
            
        # Step 2: Generate a prompt for the AI to analyze the todos and request
        from ai_services.llm.llm_service import LLMService
        llm_service = LLMService()
        
        prompt = f"""
        User wants to edit a todo with this request: "{edit_request}"
        
        Here are the user's current todos:
        {json.dumps(todos_context, indent=2)}
        
        Based on the user's request and their todos, identify:
        1. Which todo needs to be edited (provide the todo_id)
        2. What specific fields need to be updated
        
        Return ONLY a valid JSON object without explanation. The JSON should contain:
        - todo_id: The UUID of the todo to update
        - title: New title (if the user wants to change it)
        - description: New description (if the user wants to change it)
        - due_date: New due date in YYYY-MM-DD format (if the user wants to change it)
        - priority: New priority as "high", "medium", or "low" (if the user wants to change it)
        - status: New status as "pending", "in_progress", or "archived" (if the user wants to change it)
        - is_completed: Boolean true/false (if the user wants to change completion status)
        
        Include ONLY the fields that need to be updated.
        """
        
        # Call the LLM to analyze todos and user request
        analysis_response = await llm_service.generate_response(
            prompt=prompt,
            context={
                "system_prompt": "You are a helpful assistant that analyzes todo items and user requests. Identify which todo the user wants to edit and what changes they want to make. Respond with a JSON object that includes todo_id and ONLY the fields that need to be updated."
            },
            stream=False
        )
        
        # Log the LLM's response
        response_text = analysis_response.get("text", "")
        logger.info(f"LLM response: {response_text[:200]}...")
        
        # Extract the AI's suggestion
        update_info = None
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                logger.info(f"Extracted JSON from code block: {json_text[:200]}...")
            else:
                # Try to find JSON-like content
                json_pattern = r'({[^{]*"todo_id"[^}]*})'
                json_match = re.search(json_pattern, response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
                    logger.info(f"Extracted JSON using pattern: {json_text[:200]}...")
                else:
                    json_text = response_text.strip()
                    logger.info(f"Using full response as JSON: {json_text[:200]}...")
                
            # Clean up the text to make sure it's valid JSON
            json_text = re.sub(r'[^\x20-\x7E]', '', json_text)
            update_info = json.loads(json_text)
            logger.info(f"Parsed update info: {update_info}")
        except Exception as e:
            error_msg = f"Failed to parse LLM response: {str(e)}"
            logger.error(error_msg)
            await ctx.error(error_msg)
            return {"status": "error", "error": error_msg}
            
        if not update_info or "todo_id" not in update_info:
            error_msg = "AI couldn't identify which todo to update"
            logger.error(error_msg)
            await ctx.error(error_msg)
            return {"status": "error", "error": error_msg}
            
        # Step 3: Extract todo_id and determine if this is a completion status change
        todo_id = update_info.pop("todo_id", None)
        if not todo_id:
            error_msg = "No todo ID provided for update"
            logger.error(error_msg)
            await ctx.error(error_msg)
            return {"status": "error", "error": error_msg}
        
        # Check if this is a completion status update
        is_completion_update = "is_completed" in update_info
        completion_value = update_info.pop("is_completed", None)
            
        # If this is a completion update, use the dedicated completion endpoints
        if is_completion_update:
            # Define the patch function for completion endpoints
            async def patch_func(client, url, **kwargs):
                response = await client.patch(url, **kwargs)
                logger.info(f"PATCH response status: {response.status_code}")
                logger.info(f"PATCH response headers: {response.headers}")
                try:
                    logger.info(f"PATCH response text: {response.text[:500]}")
                except:
                    logger.info("Could not retrieve response text")
                return response
            
            # Determine which endpoint to use based on completion status
            completion_endpoint = f"/api/todos/{todo_id}/complete" if completion_value else f"/api/todos/{todo_id}/uncomplete"
            
            logger.info(f"Using dedicated completion endpoint: {completion_endpoint}")
            
            # Make the completion status update request
            update_result = await try_backend_urls(
                patch_func,
                completion_endpoint,
                headers=headers,
                json={}  # Empty payload for completion endpoints
            )
            
            logger.info(f"Completion update result: {json.dumps(update_result, default=str)[:200]}...")
            
            # If there are other fields to update, continue with regular update
            if update_info:
                logger.info(f"Additional fields to update: {update_info}. Proceeding with general update.")
            else:
                # If only completion status needed updating, return result
                if update_result.get("status") != "error":
                    await ctx.info(f"Todo {todo_id} completion status updated successfully")
                    return {
                        "status": "success", 
                        "message": f"Todo marked as {'completed' if completion_value else 'uncompleted'} successfully",
                        "content": update_result.get("content", {}) or update_result.get("data", {})
                    }
                else:
                    error_msg = update_result.get("error", "Unknown error updating todo completion status")
                    logger.error(f"Error updating todo completion status: {error_msg}")
                    await ctx.error(f"Error updating todo completion status: {error_msg}")
                    return {
                        "status": "error",
                        "error": error_msg,
                        "type": "api_error"
                    }
            
        # For regular updates (non-completion or additional fields after completion update)
        # Ensure we're formatting the data correctly for the Go backend
        update_data = {}
        
        # Map the fields from the LLM response to what the backend expects
        if "title" in update_info:
            update_data["title"] = update_info["title"]
            
        if "description" in update_info:
            update_data["description"] = update_info["description"]
            
        if "status" in update_info:
            update_data["status"] = update_info["status"]
            
        if "priority" in update_info:
            update_data["priority"] = update_info["priority"]
            
        if "due_date" in update_info:
            update_data["due_date"] = update_info["due_date"]
        
        # Only proceed with general update if there are fields to update
        if update_data:
            logger.info(f"Prepared update data: {update_data}")
            logger.info(f"Making PUT request to: /api/todos/{todo_id}")
                
            # Call the update tool using try_backend_urls
            async def put_func(client, url, **kwargs):
                response = await client.put(url, **kwargs)
                logger.info(f"PUT response status: {response.status_code}")
                logger.info(f"PUT response headers: {response.headers}")
                # Try to log response text if available
                try:
                    logger.info(f"PUT response text: {response.text[:500]}")
                except:
                    logger.info("Could not retrieve response text")
                return response
                
            update_result = await try_backend_urls(
                put_func,
                f"/api/todos/{todo_id}",
                headers=headers,
                json=update_data
            )
            
            # Log the result
            logger.info(f"Update result: {json.dumps(update_result, default=str)[:200]}...")
            
            # Return the result
            if update_result.get("status") != "error":
                await ctx.info(f"Todo {todo_id} updated successfully")
                return {
                    "status": "success", 
                    "message": "Todo updated successfully",
                    "content": update_result.get("content", {}) or update_result.get("data", {})
                }
            else:
                error_msg = update_result.get("error", "Unknown error updating todo")
                logger.error(f"Error updating todo: {error_msg}")
                await ctx.error(f"Error updating todo: {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg,
                    "type": "api_error"
                }
        else:
            # If we've already handled completion and there are no other fields to update
            return {
                "status": "success",
                "message": "Todo updated successfully",
            }
        
    except Exception as e:
        error_msg = f"Error in smart todo update: {str(e)}"
        logger.error(error_msg)
        await ctx.error(error_msg)
        return {"status": "error", "error": error_msg, "type": "api_error"}

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

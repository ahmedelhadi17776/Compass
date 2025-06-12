from typing import Dict, Any, List, Optional
import logging
import asyncio
from pydantic import BaseModel, Field
import json

from ai_services.llm.llm_service import LLMService
from core.mcp_state import get_mcp_client
from orchestration.prompts import SYSTEM_PROMPT
from data_layer.cache.ai_cache_manager import AICacheManager


class BaseIOSchema(BaseModel):
    """Base schema class for agent input/output following Atomic Agents patterns."""
    pass


class BaseAgent:
    """
    Base class for all AI agents in the system.
    Implements the Atomic Agents pattern for agent structure.
    """

    def __init__(self):
        self.llm_service = LLMService()
        self.logger = logging.getLogger(__name__)
        self._init_lock = asyncio.Lock()
        self.mcp_client = None

    async def _get_mcp_client(self):
        """Get MCP client, with lazy initialization."""
        if self.mcp_client is None:
            async with self._init_lock:
                if self.mcp_client is None:
                    self.logger.info(
                        "Fetching MCP client from global state for agent")
                    self.mcp_client = get_mcp_client()
                    if self.mcp_client is None:
                        self.logger.warning(
                            "MCP client not available in global state for agent")
        return self.mcp_client

    async def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Fetch available tools from MCP client with caching."""
        try:
            cached_tools = await AICacheManager.get_cached_tools()
            if cached_tools:
                self.logger.info("Retrieved tools from cache for agent")
                return cached_tools

            mcp_client = await self._get_mcp_client()
            if not mcp_client:
                self.logger.warning(
                    "Could not get MCP client, returning empty tools list")
                return []

            tools = await mcp_client.get_tools()
            self.logger.info(
                f"Retrieved {len(tools)} tools from MCP client for agent")

            for tool in tools:
                if "input_schema" in tool and "properties" in tool["input_schema"]:
                    auth_params = ["user_id", "auth_token",
                                   "token", "authorization"]
                    for param in auth_params:
                        if param in tool["input_schema"]["properties"]:
                            tool["input_schema"]["properties"].pop(param)
                    if "required" in tool["input_schema"]:
                        tool["input_schema"]["required"] = [
                            r for r in tool["input_schema"]["required"] if r not in auth_params]

            await AICacheManager.set_cached_tools(tools)
            self.logger.info("Cached tools in Redis for agent")

            return tools
        except Exception as e:
            self.logger.error(
                f"Error getting available tools for agent: {str(e)}")
            return []

    def _format_tools_for_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools into a string for the system prompt."""
        if not tools:
            return "No tools are currently available."

        tool_strings = []
        for tool in tools:
            schema_str = json.dumps(tool.get('input_schema', {}), indent=2)
            tool_str = f"- {tool['name']}: {tool.get('description', 'No description')}\n  Arguments: {schema_str}"
            tool_strings.append(tool_str)

        return "\n".join(tool_strings)

    def _extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response."""
        tool_calls = []
        start_tag = "<tool_call>"
        end_tag = "</tool_call>"

        while start_tag in text and end_tag in text:
            start = text.find(start_tag) + len(start_tag)
            end = text.find(end_tag)
            if start > -1 and end > -1:
                tool_call_text = text[start:end].strip()
                try:
                    tool_call = json.loads(tool_call_text)
                    if "name" in tool_call:
                        tool_calls.append(tool_call)
                    else:
                        self.logger.warning(
                            f"Tool call missing 'name' field: {tool_call_text}")
                except json.JSONDecodeError:
                    self.logger.error(
                        f"Failed to parse tool call: {tool_call_text}")
                text = text[end + len(end_tag):]
            else:
                break

        return tool_calls

    def _make_serializable(self, obj):
        """Convert non-serializable objects to serializable structures recursively."""
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        if isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        self.logger.warning(
            f"Converting non-serializable content type {type(obj)} to serializable form")
        try:
            if hasattr(obj, '__dict__'):
                return {k: self._make_serializable(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
            if hasattr(obj, 'text'):
                text = obj.text
                if isinstance(text, str):
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return text
                return text
            if hasattr(obj, 'data'):
                return self._make_serializable(obj.data)
            if hasattr(obj, 'content'):
                return self._make_serializable(obj.content)
            return str(obj)
        except Exception as e:
            self.logger.error(
                f"Error converting object to serializable form: {str(e)}")
            return str(obj)

    async def _get_target_data(
        self,
        target_type: str,
        target_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve data for a specific target using MCP tools.
        """
        mcp_client = await self._get_mcp_client()
        if not mcp_client:
            self.logger.error("Failed to get MCP client")
            return self._create_fallback_data(target_type, target_id)

        try:
            # Map target types to appropriate MCP tool calls
            if target_type == "todo":
                self.logger.info(
                    f"Attempting to get todo data for {target_id}")

                # Try to get todo data from the MCP
                try:
                    result = await mcp_client.call_tool("get_items", {
                        "item_type": "todos",
                        "id": target_id,
                        "user_id": user_id
                    })

                    # Check if result is valid and has content
                    if isinstance(result, dict):
                        # Check for error status first
                        if result.get("status") == "error":
                            error_msg = result.get("error", "Unknown error")
                            self.logger.warning(
                                f"Error from get_items: {error_msg}")

                            # Special handling for auth errors
                            if "HTTP 401" in error_msg or "authentication" in error_msg.lower():
                                self.logger.error(
                                    "Authentication error detected (HTTP 401)")

                            return self._create_fallback_data(target_type, target_id)

                        # Extract content if present
                        content = result.get("content")

                        # Handle different content types
                        if isinstance(content, dict) and content:
                            self.logger.info(f"Successfully got todo data")
                            return content
                        elif isinstance(content, list) and content:
                            # Try to find the specific todo in the list
                            for todo in content:
                                if isinstance(todo, dict) and todo.get("id") == target_id:
                                    self.logger.info(
                                        f"Found todo in list data")
                                    return todo
                            # If target not found but we have some data, use the first item
                            if content and isinstance(content[0], dict):
                                self.logger.warning(
                                    f"Todo {target_id} not found, using first available")
                                return content[0]

                    self.logger.warning(
                        f"Invalid or empty result for todo {target_id}")

                except Exception as e:
                    self.logger.warning(f"Error getting todo data: {str(e)}")

                # Use fallback data if we couldn't get valid data
                return self._create_fallback_data(target_type, target_id)

            elif target_type == "habit":
                # Similar pattern for habits - try get_items first
                try:
                    self.logger.info(
                        f"Trying get_items tool for habit {target_id}")
                    result = await mcp_client.call_tool("get_items", {
                        "item_type": "habits",
                        "id": target_id,
                        "user_id": user_id
                    })

                    if isinstance(result, dict):
                        # Check for error status
                        if result.get("status") == "error":
                            self.logger.warning(
                                f"Error from get_items: {result.get('error')}")
                            return self._create_fallback_data(target_type, target_id)

                        # Extract content if present
                        content = result.get("content")
                        if content:
                            self.logger.info(f"Got habit data")
                            return content
                except Exception as e:
                    self.logger.warning(
                        f"Error using get_items for habit: {str(e)}")

                # Fallback
                return self._create_fallback_data(target_type, target_id)

            elif target_type == "event":
                # Try calendar.getEvents
                try:
                    self.logger.info(
                        f"Trying calendar.getEvents for event {target_id}")
                    # Since we don't have a direct get_event tool, we need to get all events
                    # and filter for this specific one
                    result = await mcp_client.call_tool("calendar.getEvents", {
                        "start_date": "2023-01-01",  # Far back date to include all events
                        "user_id": user_id
                    })

                    if isinstance(result, dict):
                        # Check for error status
                        if result.get("status") == "error":
                            self.logger.warning(
                                f"Error from calendar.getEvents: {result.get('error')}")
                            return self._create_fallback_data(target_type, target_id)

                        # Extract events from content
                        content = result.get("content", {})
                        events = content.get("events", []) if isinstance(
                            content, dict) else []

                        if isinstance(events, list):
                            for event in events:
                                if event.get("id") == target_id:
                                    return event
                except Exception as e:
                    self.logger.warning(
                        f"Error getting calendar event: {str(e)}")

                # Fallback
                return self._create_fallback_data(target_type, target_id)

            elif target_type == "note":
                # Try notes.get
                try:
                    self.logger.info(f"Trying notes.get for note {target_id}")
                    result = await mcp_client.call_tool("notes.get", {
                        "user_id": user_id
                    })

                    if isinstance(result, dict):
                        # Check for error status
                        if result.get("status") == "error":
                            self.logger.warning(
                                f"Error from notes.get: {result.get('error')}")
                            return self._create_fallback_data(target_type, target_id)

                        # Extract content
                        content = result.get("content", {})
                        data = content.get("data", []) if isinstance(
                            content, dict) else []

                        if isinstance(data, list):
                            for note in data:
                                if note.get("id") == target_id:
                                    return note
                except Exception as e:
                    self.logger.warning(f"Error getting note: {str(e)}")

                # Fallback
                return self._create_fallback_data(target_type, target_id)

            self.logger.warning(f"Failed to get {target_type} data from MCP")
            return self._create_fallback_data(target_type, target_id)

        except Exception as e:
            self.logger.error(f"Error getting {target_type} data: {str(e)}")
            return self._create_fallback_data(target_type, target_id)

    def _create_fallback_data(self, target_type: str, target_id: str) -> Dict[str, Any]:
        """Create fallback data when actual data can't be retrieved."""
        self.logger.warning(
            f"Using fallback data for {target_type} {target_id}")

        if target_type == "todo":
            return {
                "id": target_id,
                "title": f"Todo {target_id[:8]}",
                "description": "Could not retrieve details for this todo.",
                "status": "pending",
                "priority": "medium",
                "due_date": None
            }
        elif target_type == "habit":
            return {
                "id": target_id,
                "title": f"Habit {target_id[:8]}",
                "description": "Could not retrieve details for this habit."
            }
        elif target_type == "event":
            return {
                "id": target_id,
                "title": f"Event {target_id[:8]}",
                "description": "Could not retrieve details for this event."
            }
        elif target_type == "note":
            return {
                "id": target_id,
                "title": f"Note {target_id[:8]}",
                "content": "Could not retrieve content for this note."
            }
        else:
            return {
                "id": target_id,
                "title": f"{target_type.capitalize()} {target_id[:8]}",
                "description": f"Unknown {target_type} type."
            }

    async def get_options(
        self,
        target_id: str,
        target_data: Dict[str, Any],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get AI options for a specific target.
        Should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement get_options")

    async def process(
        self,
        option_id: str,
        target_type: str,
        target_id: str,
        user_id: str,
        *,
        target_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a selected AI option.
        Should be implemented by specialized agent subclasses.
        """
        raise NotImplementedError("Subclasses must implement process")

    async def _generate_response_with_tools(
        self,
        prompt: str,
        user_id: str,
        model_parameters: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> str:
        """Generate a response, potentially using tools, but do not stream."""
        tools = await self._get_available_tools()
        formatted_tools = self._format_tools_for_prompt(tools)
        enhanced_system_prompt = SYSTEM_PROMPT.format(tools=formatted_tools)

        complete_response = await self.llm_service.generate_response(
            prompt=prompt,
            context={"system_prompt": enhanced_system_prompt},
            stream=False,
            user_id=user_id
        )

        if not isinstance(complete_response, dict):
            return "Error: Unexpected response from AI service"

        response_text = complete_response.get("text", "")
        tool_calls = self._extract_tool_calls(response_text)

        if not tool_calls:
            return response_text

        self.logger.info(
            f"Agent found {len(tool_calls)} tool calls to execute.")
        tool_results = []
        mcp_client = await self._get_mcp_client()

        if not mcp_client:
            return "Error: MCP client not available to execute tools."

        for tool_call in tool_calls:
            try:
                if auth_token:
                    if "arguments" not in tool_call:
                        tool_call["arguments"] = {}
                    tool_call["arguments"]["authorization"] = auth_token

                result = await mcp_client.call_tool(tool_call["name"], tool_call.get("arguments", {}))

                if result.get("status") == "success":
                    content = self._make_serializable(
                        result.get("content", {}))
                    tool_results.append(
                        {"tool": tool_call["name"], "result": content})
                else:
                    tool_results.append(
                        {"tool": tool_call["name"], "error": result.get("error", "Unknown error")})
            except Exception as e:
                self.logger.error(
                    f"Agent tool call execution failed: {str(e)}")
                tool_results.append(
                    {"tool": tool_call["name"], "error": str(e)})

        final_prompt = f"Based on the user query: {prompt}\nHere are the tool results: {json.dumps(tool_results, indent=2)}\nPlease provide a helpful, final response to the user."
        final_response = await self.llm_service.generate_response(
            prompt=final_prompt,
            context={
                "system_prompt": "You are IRIS, a helpful AI assistant. Format the tool results in a natural, helpful way for the user."},
            stream=False,
            user_id=user_id
        )

        if isinstance(final_response, dict):
            return final_response.get("text", "Error generating final response.")
        return "Error processing the request with tools."

    async def _generate_response(
        self,
        prompt: str,
        user_id: str,
        model_parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response using the LLM service.
        """
        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                context={"user_id": user_id},
                model_parameters=model_parameters,
                stream=False,
                user_id=user_id
            )

            if isinstance(response, dict):
                return response.get("text", "No response generated.")

            return "Error processing the request."
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return f"Error generating AI response: {str(e)}"

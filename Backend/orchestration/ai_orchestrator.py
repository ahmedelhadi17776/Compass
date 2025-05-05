from typing import Dict, Any, Optional, Union, AsyncGenerator, List
from app.schemas.message_schemas import ConversationHistory, UserMessage, AssistantMessage
from ai_services.llm.llm_service import LLMService
from orchestration.ai_registry import ai_registry
from core.mcp_state import get_mcp_client
from core.config import settings
from orchestration.langchain_memory import ConversationMemoryManager
from langchain.prompts import ChatPromptTemplate
import logging
import json
import time
import asyncio

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Iris, a powerful agentic AI assistant designed by the COMPASS engineering team. Your goal is to help users complete tasks by understanding their requests and using the appropriate tools at your disposal.

<identity>
You are designed to be helpful, efficient, and proactive in solving user problems. You have the ability to use various tools to accomplish tasks, analyze data, and provide comprehensive responses.

<core_tasks>
1. Understand the user's query by carefully analyzing their request
2. Determine which tool(s) would be most helpful to answer their query
3. Call the appropriate tool(s) with the correct parameters
4. Format and present the results in a natural, helpful way
</core_tasks>

<authentication>
Important: You have access to an authenticated context. DO NOT ask users for authentication - you already have access via JWT token.
</authentication>

<tool_calling>
You have access to the following tools:
{tools}

When you need to use a tool, follow these guidelines:
1. Only call tools when they are necessary to complete the user's request
2. Don't make redundant tool calls as these can be expensive
3. If the user's task is general or you already know the answer, just respond without calling tools
4. Format your tool calls exactly as shown below:

<tool_call>
{{"name": "tool_name", "arguments": {{"arg1": "value1", "arg2": "value2"}}}}
</tool_call>

5. Before calling each tool, briefly explain why you are calling it
6. After getting tool results, provide your response in a natural, conversational way
7. If a tool call fails, try to recover gracefully and suggest alternatives

You may need to make multiple tool calls to complete a complex task. If so, explain your step-by-step approach.
</tool_calling>

<communication_style>
- Be concise and avoid unnecessary verbosity
- Format your responses in a clear, readable way
- Refer to the user in the second person
- Be proactive in suggesting solutions the user might not have considered
- Respond directly to what was asked without unnecessary explanation
- When presenting information from tools, format it in a way that's easy to understand
</communication_style>

<problem_solving>
When tackling complex problems:
1. Break the task into smaller, manageable steps
2. Explain your approach before executing it
3. Use tools in a logical sequence to build toward the solution
4. If faced with ambiguity, make reasonable assumptions and proceed, but note these assumptions
5. If you're uncertain about a user's intent, ask clarifying questions
</problem_solving>

Remember that your primary goal is to help users accomplish their tasks efficiently and effectively.
"""


class AIOrchestrator:
    def __init__(self):
        self.llm_service = LLMService()
        self.logger = logging.getLogger(__name__)
        self._current_model_id: Optional[int] = None
        self.ai_registry = ai_registry
        self.memory_manager = ConversationMemoryManager(max_history_length=10)
        self.max_history_length = 10
        self.mcp_client = None
        self._init_lock = asyncio.Lock()

        # We'll initialize the MCP client lazily when needed
        self.logger.info(
            "AIOrchestrator initialized with lazy MCP client loading")

    async def _get_mcp_client(self):
        """Get MCP client, with lazy initialization."""
        if self.mcp_client is None:
            async with self._init_lock:
                # Check again in case another task initialized it while we were waiting
                if self.mcp_client is None:
                    self.logger.info("Fetching MCP client from global state")
                    self.mcp_client = get_mcp_client()
                    if self.mcp_client is None:
                        self.logger.warning(
                            "MCP client not available in global state")
        return self.mcp_client

    async def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Fetch available tools from MCP client."""
        try:
            mcp_client = await self._get_mcp_client()
            if not mcp_client:
                self.logger.warning(
                    "Could not get MCP client, returning empty tools list")
                return []

            tools = await mcp_client.get_tools()
            self.logger.info(f"Retrieved {len(tools)} tools from MCP client")

            # Remove any auth-related parameters since we use JWT
            for tool in tools:
                if "input_schema" in tool and "properties" in tool["input_schema"]:
                    # Remove user_id and auth-related parameters for display in the prompt
                    auth_params = ["user_id", "auth_token",
                                   "token", "authorization"]
                    for param in auth_params:
                        if param in tool["input_schema"]["properties"]:
                            tool["input_schema"]["properties"].pop(param)
                    if "required" in tool["input_schema"]:
                        tool["input_schema"]["required"] = [
                            r for r in tool["input_schema"]["required"] if r not in auth_params]

            return tools
        except Exception as e:
            self.logger.error(f"Error getting available tools: {str(e)}")
            return []

    def _format_tools_for_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools into a string for the system prompt."""
        if not tools:
            return "No tools are currently available."

        tool_strings = []
        for tool in tools:
            # Format tool input schema in a more readable way
            schema_str = json.dumps(tool.get('input_schema', {}), indent=2)
            tool_str = f"- {tool['name']}: {tool.get('description', 'No description')}\n  Arguments: {schema_str}"
            tool_strings.append(tool_str)

        return "\n".join(tool_strings)

    async def process_request(self, user_input: str, user_id: int, domain: Optional[str] = None, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Process an AI request with MCP integration."""
        try:
            start_time = time.time()
            self.logger.info(
                f"Processing request for user {user_id} in domain {domain or 'default'}")

            # Get conversation history using LangChain memory
            messages = self.memory_manager.get_langchain_messages(user_id)
            self.logger.debug(
                f"Retrieved {len(messages)} conversation history messages")

            # Get available tools and format system prompt
            tools = await self._get_available_tools()
            formatted_tools = self._format_tools_for_prompt(tools)
            system_prompt = SYSTEM_PROMPT.format(tools=formatted_tools)

            # Generate initial LLM response with LangChain chat history
            response = await self.llm_service.generate_response(
                prompt=user_input,
                context={
                    "system_prompt": system_prompt,
                    "conversation_history": messages
                }
            )

            # Ensure response is a dictionary
            if not isinstance(response, dict):
                # If it's a streaming response (AsyncGenerator), create a dictionary
                self.logger.warning(
                    "Received non-dictionary response, converting to dictionary")
                response = {
                    "text": "Response generated via streaming",
                    "confidence": 0.5
                }

            # Extract tool calls if any
            response_text = response.get("text", "")
            tool_calls = self._extract_tool_calls(response_text)
            self.logger.info(
                f"Extracted {len(tool_calls)} tool calls from response")

            final_response = response_text
            tool_info = None

            # Process tool calls if present
            if tool_calls:
                tool_results = []
                last_tool_call = None

                for idx, tool_call in enumerate(tool_calls):
                    try:
                        self.logger.info(
                            f"Processing tool call {idx+1}/{len(tool_calls)}: {tool_call['name']}")

                        # Add authorization if provided
                        if auth_token:
                            if "arguments" not in tool_call:
                                tool_call["arguments"] = {}
                            tool_call["arguments"]["authorization"] = auth_token

                        # Get MCP client safely
                        mcp_client = await self._get_mcp_client()
                        if mcp_client is None:
                            raise ValueError("MCP client is not available")

                        # Execute the tool call with retry logic built into the client
                        result = await mcp_client.call_tool(
                            tool_call["name"],
                            tool_call["arguments"]
                        )

                        # Check if the tool call was successful
                        if result.get("status") == "success":
                            self.logger.info(
                                f"Tool call {tool_call['name']} succeeded")

                            # Process the content to ensure it's serializable
                            content = result.get("content", {})

                            # Process any complex content recursively
                            content = self._make_serializable(content)

                            tool_results.append({
                                "tool": tool_call["name"],
                                "result": content
                            })
                            last_tool_call = {
                                "name": tool_call["name"],
                                "arguments": tool_call["arguments"],
                                "success": True
                            }
                        else:
                            self.logger.warning(
                                f"Tool call {tool_call['name']} failed: {result.get('error', 'Unknown error')}")
                            tool_results.append({
                                "tool": tool_call["name"],
                                "error": result.get("error", "Unknown error")
                            })
                            last_tool_call = {
                                "name": tool_call["name"],
                                "arguments": tool_call["arguments"],
                                "success": False
                            }
                    except Exception as e:
                        self.logger.error(
                            f"Tool call execution failed: {str(e)}")
                        tool_results.append({
                            "tool": tool_call["name"],
                            "error": str(e)
                        })
                        last_tool_call = {
                            "name": tool_call["name"],
                            "arguments": tool_call["arguments"],
                            "success": False
                        }

                # Generate final response with tool results
                if tool_results:
                    self.logger.info(
                        "Generating final response with tool results")
                    
                    # Log the exact tool results being sent to LLM
                    self.logger.info(f"Tool results being sent to LLM for final response: {json.dumps(tool_results, indent=2)}")
                    
                    prompt_for_llm = f"Based on the user query: {user_input}\nHere are the tool results: {json.dumps(tool_results, indent=2)}\nPlease provide a helpful response."
                    self.logger.info(f"Full prompt being sent to LLM: {prompt_for_llm}")
                    
                    final_result = await self.llm_service.generate_response(
                        prompt=prompt_for_llm,
                        context={
                            "system_prompt": "Format the tool results in a natural, helpful way for the user."
                        }
                    )
                    # Log the LLM's response
                    self.logger.info(f"LLM final response: {final_result}")
                    
                    # Ensure this is also a dictionary
                    if isinstance(final_result, dict):
                        final_response = final_result.get("text", "")
                    else:
                        final_response = "Results processed successfully."
                    tool_info = last_tool_call

            # Update conversation history with LangChain memory
            self._update_conversation_history(
                user_id, user_input, final_response)

            execution_time = time.time() - start_time
            self.logger.info(
                f"Request processed in {execution_time:.2f} seconds")

            return {
                "response": final_response,
                "tool_used": tool_info["name"] if tool_info else None,
                "tool_args": tool_info["arguments"] if tool_info else None,
                "tool_success": tool_info["success"] if tool_info else None,
                "description": "Process user request",
                "rag_used": False,
                "cached": False,
                "confidence": response.get("confidence", 0.0),
                "execution_time": execution_time
            }

        except Exception as e:
            self.logger.error(
                f"Error in process_request: {str(e)}", exc_info=True)
            return {
                "response": f"I'm sorry, but I encountered an error: {str(e)}",
                "tool_used": None,
                "tool_args": None,
                "tool_success": False,
                "description": "Error processing request",
                "rag_used": False,
                "cached": False,
                "confidence": 0.0,
                "error": True,
                "error_message": str(e)
            }

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
                    # Validate required fields
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

    def _get_conversation_history(self, user_id: int) -> ConversationHistory:
        """Get conversation history for a user using LangChain memory."""
        return self.memory_manager.convert_to_chat_history(user_id)

    def _update_conversation_history(self, user_id: int, prompt: str, response: str) -> None:
        """Update conversation history with new messages using LangChain memory."""
        self.memory_manager.add_user_message(user_id, prompt)
        self.memory_manager.add_ai_message(user_id, response)

    def _make_serializable(self, obj):
        """Convert non-serializable objects to serializable structures recursively."""
        # Base case: object is already a basic type
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj

        # Handle lists recursively
        if isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]

        # Handle dictionaries recursively
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}

        # Handle TextContent or other special objects
        self.logger.warning(
            f"Converting non-serializable content type {type(obj)} to serializable form")

        try:
            # Try to convert to a dictionary if the object has specific attributes
            if hasattr(obj, '__dict__'):
                return {k: self._make_serializable(v) for k, v in obj.__dict__.items() if not k.startswith('_')}

            # Handle TextContent specifically
            if hasattr(obj, 'text'):
                text = obj.text
                # Try to parse JSON
                if isinstance(text, str):
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return text
                return text

            # Handle other attribute combinations
            if hasattr(obj, 'data'):
                return self._make_serializable(obj.data)

            if hasattr(obj, 'content'):
                return self._make_serializable(obj.content)

            # Final fallback: convert to string
            return str(obj)

        except Exception as e:
            self.logger.error(
                f"Error converting object to serializable form: {str(e)}")
            return str(obj)

from typing import Dict, Any, Optional, Union, AsyncGenerator, List
from Backend.app.schemas.message_schemas import ConversationHistory, UserMessage, AssistantMessage
from Backend.ai_services.llm.llm_service import LLMService
from Backend.orchestration.ai_registry import ai_registry
from Backend.core.mcp_state import get_mcp_client
from Backend.core.config import settings
from Backend.orchestration.langchain_memory import ConversationMemoryManager
from langchain.prompts import ChatPromptTemplate
import logging
import json
import time

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful AI assistant with access to various tools. Your task is to:
1. Understand the user's query
2. Determine which tool(s) would be most helpful to answer their query
3. Call the appropriate tool(s)
4. Format and present the results in a helpful way

Important: You have access to an authenticated context. DO NOT ask users for authentication - you already have access via JWT token.

Available tools:
{tools}

When you need to use a tool, format your response like this:
<tool_call>
{{"name": "tool_name", "arguments": {{"arg1": "value1", "arg2": "value2"}}}}
</tool_call>

After getting tool results, provide your response in a natural, conversational way.
"""

class AIOrchestrator:
    def __init__(self):
        self.llm_service = LLMService()
        self.logger = logging.getLogger(__name__)
        self._current_model_id: Optional[int] = None
        self.ai_registry = ai_registry
        self.memory_manager = ConversationMemoryManager(max_history_length=10)
        self.max_history_length = 10
        self.mcp_client = get_mcp_client()

    async def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Fetch available tools from MCP client."""
        if self.mcp_client:
            tools = await self.mcp_client.get_tools()
            # Remove any auth-related parameters since we use JWT
            for tool in tools:
                if "input_schema" in tool and "properties" in tool["input_schema"]:
                    # Remove user_id and auth-related parameters
                    auth_params = ["user_id", "auth_token", "token"]
                    for param in auth_params:
                        if param in tool["input_schema"]["properties"]:
                            tool["input_schema"]["properties"].pop(param)
                    if "required" in tool["input_schema"]:
                        tool["input_schema"]["required"] = [r for r in tool["input_schema"]["required"] if r not in auth_params]
            return tools
        return []

    def _format_tools_for_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools into a string for the system prompt."""
        tool_strings = []
        for tool in tools:
            tool_str = f"- {tool['name']}: {tool['description']}\n  Arguments: {json.dumps(tool['input_schema'])}"
            tool_strings.append(tool_str)
        return "\n".join(tool_strings)

    async def process_request(self, user_input: str, user_id: int, domain: Optional[str] = None) -> Dict[str, Any]:
        """Process an AI request with MCP integration."""
        try:
            # Get conversation history using LangChain memory
            messages = self.memory_manager.get_langchain_messages(user_id)

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

            # Extract tool calls if any
            tool_calls = self._extract_tool_calls(response.get("text", ""))
            
            final_response = response.get("text", "")
            tool_info = None
            
            # Process tool calls if present
            if tool_calls:
                tool_results = []
                last_tool_call = None
                for tool_call in tool_calls:
                    try:
                        result = await self.mcp_client.invoke_tool(
                            tool_call["name"],
                            tool_call["arguments"]
                        )
                        tool_results.append({
                            "tool": tool_call["name"],
                            "result": result
                        })
                        last_tool_call = {
                            "name": tool_call["name"],
                            "arguments": tool_call["arguments"],
                            "success": True
                        }
                    except Exception as e:
                        self.logger.error(f"Tool call failed: {str(e)}")
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
                    final_response = await self.llm_service.generate_response(
                        prompt=f"Based on the user query: {user_input}\nHere are the tool results: {json.dumps(tool_results, indent=2)}\nPlease provide a helpful response.",
                        context={
                            "system_prompt": "Format the tool results in a natural, helpful way for the user."
                        }
                    )
                    final_response = final_response.get("text", "")
                    tool_info = last_tool_call

            # Update conversation history with LangChain memory
            self._update_conversation_history(user_id, user_input, final_response)

            return {
                "response": final_response,
                "tool_used": tool_info["name"] if tool_info else None,
                "tool_args": tool_info["arguments"] if tool_info else None,
                "tool_success": tool_info["success"] if tool_info else None,
                "description": "Process user request",
                "rag_used": False,
                "cached": False,
                "confidence": response.get("confidence", 0.0)
            }

        except Exception as e:
            self.logger.error(f"Error in process_request: {str(e)}", exc_info=True)
            raise

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
                    tool_calls.append(tool_call)
                except json.JSONDecodeError:
                    self.logger.error(f"Failed to parse tool call: {tool_call_text}")
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

# Backend/mcp_integration/client.py

from typing import Optional, Dict, Any, List, cast
from dataclasses import dataclass
from contextlib import AsyncExitStack
import traceback
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CreateMessageRequestParams, CreateMessageResult, TextContent
from datetime import datetime
import logging
import json
import os
import asyncio
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletion
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai._types import NotGiven
from Backend.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Represents an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class Resource:
    """Represents an MCP resource."""
    name: str
    description: str
    schema: Dict[str, Any]


class MCPClient:
    """Model Context Protocol client for communicating with Go backend."""

    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        # Initialize OpenAI client with settings
        self.llm = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_api_base_url
        )
        self.model = settings.llm_model_name
        self.tools: List[Dict[str, Any]] = []
        self.messages: List[Dict[str, Any]] = []
        self.logger = logger

    async def connect_to_server(self, server_script_path: str):
        try:
            is_python = server_script_path.endswith(".py")
            is_js = server_script_path.endswith(".js")
            is_go = server_script_path.endswith(".go")
            if not (is_python or is_js or is_go):
                raise ValueError("Server script must be a .py or .js or .go file")

            command = "python" if is_python else "node" if is_js else "go" if is_go else None
            if command is None:
                raise ValueError("Unsupported server script type")

            server_params = StdioServerParameters(
                command=command, args=[server_script_path], env=None
            )

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )

            await self.session.initialize()

            self.logger.info("Connected to MCP server")

            mcp_tools = await self.get_mcp_tools()
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in mcp_tools
            ]

            self.logger.info(
                f"Available tools: {[tool['name'] for tool in self.tools]}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error connecting to MCP server: {e}")
            traceback.print_exc()
            raise

    async def get_mcp_tools(self):
        try:
            if not self.session:
                raise RuntimeError("MCP session not initialized")
            response = await self.session.list_tools()
            return response.tools
        except Exception as e:
            self.logger.error(f"Error getting MCP tools: {e}")
            raise

    async def process_query(self, query: str):
        try:
            self.logger.info(f"Processing query: {query}")
            user_message = {"role": "user", "content": query}
            self.messages = [user_message]

            while True:
                response = await self.call_llm()
                message = cast(ChatCompletionMessage,
                               response.choices[0].message)

                # Handle text response
                if not message.function_call:
                    assistant_message = {
                        "role": "assistant",
                        "content": message.content,
                    }
                    self.messages.append(assistant_message)
                    await self.log_conversation()
                    break

                # Handle tool calls
                assistant_message = {
                    "role": "assistant",
                    "content": message.content,
                    "function_call": message.function_call
                }
                self.messages.append(assistant_message)
                await self.log_conversation()

                # Process tool calls
                function_call = message.function_call
                if function_call:
                    tool_name = function_call.name
                    try:
                        tool_args = json.loads(function_call.arguments)
                        self.logger.info(
                            f"Calling tool {tool_name} with args {tool_args}"
                        )
                        result = await self.call_tool(tool_name, tool_args)
                        self.logger.info(
                            f"Tool {tool_name} result: {result}...")
                        self.messages.append(
                            {
                                "role": "function",
                                "name": tool_name,
                                "content": json.dumps(result.content if hasattr(result, 'content') else result)
                            }
                        )
                        await self.log_conversation()
                    except Exception as e:
                        self.logger.error(
                            f"Error calling tool {tool_name}: {e}")
                        raise

            return self.messages

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            raise

    async def call_llm(self):
        try:
            self.logger.info("Calling LLM")
            messages = cast(List[ChatCompletionMessageParam], self.messages)
            completion = await asyncio.to_thread(
                self.llm.chat.completions.create,
                model=self.model,
                messages=messages,
                functions=[{
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                } for tool in self.tools],
                function_call="auto",
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens
            )
            return cast(ChatCompletion, completion)
        except Exception as e:
            self.logger.error(f"Error calling LLM: {e}")
            raise

    async def cleanup(self):
        try:
            await self.exit_stack.aclose()
            self.logger.info("Disconnected from MCP server")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            traceback.print_exc()
            raise

    async def log_conversation(self):
        os.makedirs("conversations", exist_ok=True)
        serializable_conversation = []

        for message in self.messages:
            try:
                serializable_message = {
                    "role": message["role"],
                    "content": message.get("content", "")
                }

                if "name" in message:
                    serializable_message["name"] = message["name"]
                if "function_call" in message:
                    serializable_message["function_call"] = message["function_call"]

                serializable_conversation.append(serializable_message)
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
                self.logger.debug(f"Message content: {message}")
                raise

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join(
            "conversations", f"conversation_{timestamp}.json")

        try:
            with open(filepath, "w") as f:
                json.dump(serializable_conversation, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error writing conversation to file: {str(e)}")
            self.logger.debug(
                f"Serializable conversation: {serializable_conversation}")
            raise

    async def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from the MCP server."""
        return self.tools

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information through MCP."""
        return await self.call_method("user.getInfo", {
            "user_id": user_id
        })

    async def get_user_context(self, user_id: str, domain: str) -> Dict[str, Any]:
        """Get user context through MCP."""
        return await self.call_method("user.getContext", {
            "user_id": user_id,
            "domain": domain
        })

    async def create_entity(self, entity_type: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create an entity through MCP."""
        return await self.call_method(f"{entity_type}.create", {
            "user_id": user_id,
            "data": data
        })

    async def update_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an entity through MCP."""
        return await self.call_method(f"{entity_type}.update", {
            "user_id": user_id,
            "entity_id": entity_id,
            "data": data
        })

    async def delete_entity(self, entity_type: str, entity_id: str, user_id: str) -> Dict[str, Any]:
        """Delete an entity through MCP."""
        return await self.call_method(f"{entity_type}.delete", {
            "user_id": user_id,
            "entity_id": entity_id
        })

    async def handle_sampling_message(self, message: CreateMessageRequestParams) -> CreateMessageResult:
        """Handle sampling messages from the MCP server."""
        return CreateMessageResult(
            role="assistant",
            content=TextContent(
                type="text",
                text="Response from Python backend",
            ),
            model="gpt-4",
            stopReason="endTurn",
        )

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        if not self.session:
            raise RuntimeError("MCP session not initialized")
        return await self.session.call_tool(tool_name, tool_args)

    async def call_method(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a method on the MCP server."""
        try:
            if not self.session:
                raise RuntimeError("MCP session not initialized")
            return await self.session.call_tool(method, params)
        except Exception as e:
            self.logger.error(f"Method call failed for {method}: {str(e)}")
            raise

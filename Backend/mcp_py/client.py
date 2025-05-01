# Backend/mcp_integration/client.py

from typing import Optional, Dict, Any, List, cast
from dataclasses import dataclass
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import types, StdioServerParameters
from datetime import datetime
import logging
import json
import os
import asyncio
import sys
import subprocess
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from mcp.types import JSONRPCMessage
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai._types import NotGiven
from Backend.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mcp_client.log')
    ]
)
logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4"


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
        """Initialize the MCP client."""
        self.session: Optional[ClientSession] = None
        self.logger = logger
        self._running = False
        self._connection_task = None
        self.tools: List[Tool] = []
        self.process: Optional[subprocess.Popen] = None

    async def connect_to_server(self, server_script_path: str):
        """Connect to the MCP server."""
        try:
            # Validate server script path
            if not os.path.exists(server_script_path):
                raise ValueError(
                    f"Server script not found at {server_script_path}")

            self.logger.info(
                f"Connecting to MCP server at {server_script_path}")

            # Create server parameters
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[server_script_path],
                env=os.environ.copy()
            )

            # Start connection in background task
            self._running = True
            self._connection_task = asyncio.create_task(
                self._maintain_connection(server_params))
            self.logger.info("Started MCP client connection task")

        except Exception as e:
            self.logger.error(
                f"Failed to connect to MCP server: {str(e)}", exc_info=True)
            raise

    async def _maintain_connection(self, server_params: StdioServerParameters):
        """Maintain the connection to the MCP server."""
        while self._running:
            try:
                self.logger.info("Establishing connection to MCP server...")

                async with stdio_client(server_params) as (read, write):
                    self.session = ClientSession(read, write)
                    await self.session.initialize()
                    self.logger.info("Connected to MCP server successfully")

                    # Initialize tools
                    tools_response = await self.session.list_tools()
                    self.tools = [Tool(
                        name=t.name,
                        description=t.description or "",
                        input_schema=t.inputSchema
                    ) for t in tools_response.tools]
                    self.logger.info(f"Initialized {len(self.tools)} tools")

                    # Keep connection alive until cleanup is called
                    while self._running:
                        await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Connection error: {str(e)}", exc_info=True)
                if self._running:
                    # Wait before retrying
                    await asyncio.sleep(5)
            finally:
                if self.session:
                    self.session = None

    async def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up MCP client...")
        self._running = False
        if self._connection_task:
            try:
                await self._connection_task
            except Exception as e:
                self.logger.error(
                    f"Error during connection task cleanup: {str(e)}", exc_info=True)
        self.session = None
        self.logger.info("MCP client cleanup complete")

    async def invoke_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        try:
            self.logger.info(f"Calling tool {name} with args: {arguments}")
            result = await self.session.call_tool(name, arguments=arguments or {})
            return {
                "status": "success",
                "content": str(result)
            }
        except Exception as e:
            self.logger.error(
                f"Error calling tool {name}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from the MCP server."""
        return [{"name": t.name, "description": t.description, "input_schema": t.input_schema} for t in self.tools]

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information through MCP."""
        return await self.invoke_tool("user.getInfo", {"user_id": user_id})

    async def get_user_context(self, user_id: str, domain: str) -> Dict[str, Any]:
        """Get user context through MCP."""
        return await self.invoke_tool("user.getContext", {
            "user_id": user_id,
            "domain": domain
        })

    async def create_entity(self, entity_type: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create an entity through MCP."""
        return await self.invoke_tool(f"{entity_type}.create", {
            "user_id": user_id,
            "data": data
        })

    async def update_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an entity through MCP."""
        return await self.invoke_tool(f"{entity_type}.update", {
            "user_id": user_id,
            "entity_id": entity_id,
            "data": data
        })

    async def delete_entity(self, entity_type: str, entity_id: str, user_id: str) -> Dict[str, Any]:
        """Delete an entity through MCP."""
        return await self.invoke_tool(f"{entity_type}.delete", {
            "user_id": user_id,
            "entity_id": entity_id
        })

    async def handle_sampling_message(self, message: types.CreateMessageRequestParams) -> types.CreateMessageResult:
        """Handle sampling messages from the MCP server."""
        return types.CreateMessageResult(
            role="assistant",
            content=types.TextContent(
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

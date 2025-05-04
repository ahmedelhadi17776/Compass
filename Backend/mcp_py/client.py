# Backend/mcp_integration/client.py

from typing import Optional, Dict, Any, List
import logging
import json
import os
import asyncio
import sys
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters
import threading
from core.config import settings

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

# Set Windows-compatible event loop policy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logger.info("Set Windows-compatible event loop policy in client")


class MCPClient:
    """Model Context Protocol client for communicating with MCP server."""

    def __init__(self):
        """Initialize the MCP client."""
        self.session: Optional[ClientSession] = None
        self.logger = logger
        self._running = False
        self._connection_task = None
        self.tools: List[Dict[str, Any]] = []

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
        retry_count = 0
        max_retries = 3

        while self._running and retry_count < max_retries:
            try:
                self.logger.info("Establishing connection to MCP server...")

                async with stdio_client(server_params) as (read, write):
                    self.session = ClientSession(read, write)
                    await self.session.initialize()
                    self.logger.info("Connected to MCP server successfully")

                    # Initialize tools
                    tools_response = await self.session.list_tools()
                    self.tools = [
                        {
                            "name": t.name,
                            "description": t.description or "",
                            "input_schema": t.inputSchema
                        } for t in tools_response.tools
                    ]
                    self.logger.info(f"Initialized {len(self.tools)} tools")

                    # Keep connection alive until cleanup is called
                    while self._running:
                        await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Connection error: {str(e)}", exc_info=True)
                retry_count += 1
                if self._running and retry_count < max_retries:
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

    async def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from the MCP server."""
        return self.tools

    async def call_tool(self, tool_name: str, tool_args: Optional[Dict[str, Any]] = None):
        """Call a tool on the MCP server."""
        if not self.session:
            self.logger.error("No active session to call tool")
            return {"status": "error", "error": "No active MCP session"}

        try:
            # Log warning for invalid authentication tokens but proceed
            if tool_args and "authorization" in tool_args:
                auth = tool_args.get("authorization")
                if not auth or auth == "Bearer undefined" or auth == "Bearer null":
                    self.logger.warning(
                        f"Missing or invalid authorization token: {auth} - proceeding without authentication")
                    # Continue processing without blocking

            self.logger.info(
                f"Calling tool {tool_name} with args: {tool_args}")
            result = await self.session.call_tool(tool_name, arguments=tool_args or {})

            # Log successful response
            if isinstance(result, dict):
                result_str = str(result)[
                    :100] + "..." if len(str(result)) > 100 else str(result)
            else:
                result_str = str(result)[
                    :100] + "..." if len(str(result)) > 100 else str(result)
            self.logger.info(f"Tool {tool_name} returned: {result_str}")

            return {
                "status": "success",
                "content": str(result)
            }
        except Exception as e:
            self.logger.error(
                f"Error calling tool {tool_name}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

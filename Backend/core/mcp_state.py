"""Module for storing global MCP client state."""
from typing import Optional
from mcp_py.client import MCPClient

# Global MCP client instance
mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> Optional[MCPClient]:
    """Get the global MCP client instance."""
    return mcp_client


def set_mcp_client(client: MCPClient) -> None:
    """Set the global MCP client instance."""
    global mcp_client
    mcp_client = client

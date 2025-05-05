"""Module for storing global MCP client state."""
from typing import Optional

_mcp_client = None

def get_mcp_client():
    """Get the global MCP client instance."""
    return _mcp_client

def set_mcp_client(client) -> None:
    """Set the global MCP client instance."""
    global _mcp_client
    _mcp_client = client

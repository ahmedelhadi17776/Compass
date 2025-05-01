import asyncio
import sys
import os
import json
from Backend.mcp_py.client import MCPClient
from Backend.core.config import settings

# Set Windows-compatible event loop policy if needed
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_tool(tool_name, arguments=None):
    """Test a specific MCP tool with arguments."""
    try:
        # Get the path to the server script
        backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Backend")
        server_path = os.path.join(backend_dir, "mcp_py", "server.py")
        
        print(f"Initializing MCP client to connect to server at: {server_path}")
        
        # Initialize MCP client
        client = MCPClient()
        await client.connect_to_server(server_path)
        print("Connected to MCP server")
        
        # List available tools
        tools = await client.get_tools()
        print("\nAvailable tools:")
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")
        
        # Call the specified tool
        print(f"\nCalling tool: {tool_name} with arguments: {arguments}")
        result = await client.invoke_tool(tool_name, arguments)
        
        # Format the output
        if result.get("status") == "success":
            content = result.get("content")
            # Try to parse JSON content if it's a string that looks like JSON
            if isinstance(content, str) and content.strip().startswith('{'):
                try:
                    parsed_content = json.loads(content)
                    print("\nResult:")
                    print(json.dumps(parsed_content, indent=2))
                except json.JSONDecodeError:
                    print("\nResult:")
                    print(content)
            else:
                print("\nResult:")
                print(content)
        else:
            print("\nError:")
            print(result.get("error", "Unknown error"))
        
        # Clean up
        await client.cleanup()
        print("\nTest completed.")
    
    except Exception as e:
        print(f"Error testing tool: {str(e)}")

if __name__ == "__main__":
    # Get tool name and arguments from command line (if provided)
    if len(sys.argv) > 1:
        tool_name = sys.argv[1]
        args = {}
        if len(sys.argv) > 2:
            try:
                args = json.loads(sys.argv[2])
            except json.JSONDecodeError:
                print("Error: Arguments must be valid JSON")
                sys.exit(1)
    else:
        # Default test: ai.model.info
        tool_name = "ai.model.info"
        args = {"name": "gpt-4"}
    
    # Run the test
    print(f"Testing tool: {tool_name}")
    asyncio.run(test_tool(tool_name, args)) 
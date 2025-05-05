import asyncio
import json
import os
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client

from ai_services.llm.llm_service import LLMService
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.llm_service = LLMService()

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
        # Store the context managers so they stay alive
        self._streams_context = sse_client(url=server_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session: ClientSession = await self._session_context.__aenter__()

        # Initialize
        await self.session.initialize()

        # List available tools to verify connection
        print("Initialized SSE client...")
        print("Listing tools...")
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def cleanup(self):
        """Properly clean up the session and streams"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

    async def process_query(self, query: str) -> str:
        """Process a query using LLM service and available tools"""
        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        # Create a system prompt that encourages tool usage
        system_prompt = """You are a helpful AI assistant with access to several tools. 
When a user asks for information that can be retrieved using one of your tools, YOU MUST USE THE APPROPRIATE TOOL.
Do not make up responses or say you don't have access - use the tools available to you.
When using tools, you must format your response as a JSON object with "tool_calls" array containing objects with "name" and "arguments" fields.

Available tools:
{}

Example tool call format:
{{"text": "I'll get that information for you.", "tool_calls": [{{"name": "get_todos", "arguments": {{"status": "pending"}}}}]}}

Remember:
1. Always use tools when they match the user's request
2. Don't apologize for using tools
3. Don't say you don't have access - use the tools
4. Format the tool results nicely for the user""".format(
            "\n".join(f"- {tool['name']}: {tool['description']}" for tool in available_tools)
        )

        # Initialize conversation messages
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": query
            }
        ]

        # Initial LLM API call
        response = await self.llm_service.generate_response(
            prompt=query,
            context={
                "system_prompt": system_prompt,
                "conversation_history": messages,
                "tools": available_tools
            }
        )

        # Process response and handle tool calls
        final_text = []

        try:
            # Try to parse response as JSON if it's a string
            if isinstance(response, str):
                response = json.loads(response)
            
            if isinstance(response, dict):
                if "text" in response:
                    final_text.append(response["text"])
                
                # Handle tool calls
                if "tool_calls" in response:
                    for tool_call in response["tool_calls"]:
                        tool_name = tool_call["name"]
                        tool_args = tool_call.get("arguments", {})
                        
                        # Execute tool call
                        result = await self.session.call_tool(tool_name, tool_args)
                        final_text.append(f"\nTool Result: {result.content}")

                        # Add messages to conversation history
                        messages.extend([
                            {
                                "role": "assistant",
                                "content": response["text"]
                            },
                            {
                                "role": "system",
                                "content": f"Tool {tool_name} returned: {result.content}"
                            }
                        ])

                        # Get final response to format tool results
                        final_response = await self.llm_service.generate_response(
                            prompt=f"Please format this tool result nicely: {result.content}",
                            context={
                                "system_prompt": system_prompt,
                                "conversation_history": messages,
                                "tools": available_tools
                            }
                        )
                        
                        if isinstance(final_response, dict) and "text" in final_response:
                            final_text.append(final_response["text"])
                        elif isinstance(final_response, str):
                            final_text.append(final_response)
                else:
                    # If no tool calls but response has text, try to make a tool call based on the query
                    if "todos" in query.lower():
                        result = await self.session.call_tool("get_todos", {})
                        final_text.append(f"\nTool Result: {result.content}")
            else:
                final_text.append(str(response))

        except Exception as e:
            final_text.append(f"Error processing response: {str(e)}")
            # Fallback to direct tool call for todo-related queries
            if "todos" in query.lower():
                try:
                    result = await self.session.call_tool("get_todos", {})
                    final_text.append(f"\nTool Result: {result.content}")
                except Exception as e2:
                    final_text.append(f"Error calling tool: {str(e2)}")

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run client.py <URL of SSE MCP server (i.e. http://localhost:8080/sse)>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_sse_server(server_url=sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys
    asyncio.run(main())
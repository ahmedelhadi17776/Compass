from fastapi import FastAPI, Request, HTTPException
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount
from Backend.orchestration.ai_orchestrator import AIOrchestrator
from Backend.core.config import settings
from typing import Dict, Any, Optional, AsyncIterator, Union, AsyncGenerator
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Initialize FastMCP server
mcp = FastMCP("compass")

# Create SSE transport instance
sse = SseServerTransport("/messages/")

# Mount the /messages path to handle SSE message posting
app.router.routes.append(Mount("/messages", app=sse.handle_post_message))


@app.get("/sse")
async def handle_sse(request: Request):
    """SSE endpoint that connects to the MCP server"""
    async with sse.connect_sse(request.scope, request.receive, request._send) as (
        read_stream,
        write_stream,
    ):
        # Run the MCP server with the established streams
        await mcp._mcp_server.run(
            read_stream,
            write_stream,
            mcp._mcp_server.create_initialization_options(),
        )


def setup_mcp_server(app: Optional[FastAPI] = None):
    """Setup and return the MCP server instance"""
    if app is not None:
        # Mount the /messages path to handle SSE message posting on the main app
        app.router.routes.append(
            Mount("/messages", app=sse.handle_post_message))
        # Add the SSE endpoint to the main app
        app.get("/sse")(handle_sse)
    return mcp


@mcp.tool("ai.process")
async def process_ai_request(
    prompt: str,
    user_id: int,
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """Process an AI request through MCP."""
    try:
        orchestrator = AIOrchestrator()
        result = await orchestrator.process_request(
            user_input=prompt,
            user_id=user_id,
            domain=domain or "default"
        )
        return result
    except Exception as e:
        logger.error(f"Error processing AI request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp.tool("ai.stream")
async def stream_ai_response(
    prompt: str,
    user_id: int,
    domain: Optional[str] = None
) -> StreamingResponse:
    """Stream AI responses through MCP."""
    try:
        orchestrator = AIOrchestrator()

        async def generate() -> AsyncIterator[str]:
            response = await orchestrator.llm_service.generate_response(
                prompt=prompt,
                context={"user_id": user_id,
                         "domain": domain or "default"},
                stream=True
            )

            if isinstance(response, AsyncGenerator):
                async for chunk in response:
                    yield chunk
            elif isinstance(response, dict):
                yield response.get("text", "")
            else:
                yield str(response)

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Error streaming AI response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

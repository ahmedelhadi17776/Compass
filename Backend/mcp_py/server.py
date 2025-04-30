from fastapi import FastAPI, Request, HTTPException
from mcp.server.fastmcp import FastMCP, Context
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

# Initialize FastMCP server with proper configuration
mcp = FastMCP(
    name="compass-ai",
    version="1.0.0",
    description="COMPASS AI Service MCP Server"
)

# Create SSE transport instance
sse = SseServerTransport("/mcp/sse")

# Mount the SSE endpoint for MCP
app.router.routes.append(Mount("/mcp/sse", app=sse.handle_post_message))


@mcp.tool("ai.process")
async def process_ai_request(
    ctx: Context,
    prompt: str,
    user_id: str,
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """Process an AI request through MCP."""
    try:
        orchestrator = AIOrchestrator()
        result = await orchestrator.process_request(
            user_input=prompt,
            user_id=int(user_id),
            domain=domain or "default"
        )
        return result
    except Exception as e:
        logger.error(f"Error processing AI request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@mcp.tool("ai.stream")
async def stream_ai_response(
    ctx: Context,
    prompt: str,
    user_id: str,
    domain: Optional[str] = None
) -> AsyncIterator[str]:
    """Stream AI responses through MCP."""
    try:
        orchestrator = AIOrchestrator()
        response = await orchestrator.llm_service.generate_response(
            prompt=prompt,
            context={"user_id": user_id, "domain": domain or "default"},
            stream=True
        )

        if isinstance(response, AsyncGenerator):
            async for chunk in response:
                yield chunk
        elif isinstance(response, dict):
            yield response.get("text", "")
        else:
            yield str(response)
    except Exception as e:
        logger.error(f"Error streaming AI response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def setup_mcp_server(app: Optional[FastAPI] = None):
    """Setup and return the MCP server instance"""
    if app is not None:
        # Mount the SSE endpoint for MCP on the main app
        app.router.routes.append(
            Mount("/mcp/sse", app=sse.handle_post_message))
    return mcp


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

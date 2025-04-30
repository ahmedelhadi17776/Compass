from fastapi import FastAPI
from contextlib import asynccontextmanager
from Backend.api.ai_routes import router as ai_router
from Backend.core.config import settings
from Backend.mcp_py.client import MCPClient
from Backend.core.mcp_state import set_mcp_client
import uvicorn
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("Starting up COMPASS AI Service")
    try:
        # Initialize MCP client
        mcp_client = MCPClient()
        await mcp_client.connect_to_server(settings.go_backend_url)
        set_mcp_client(mcp_client)
        logger.info("MCP client initialized successfully")

        # Initialize any other startup services here
        logger.info("AI Service initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

    yield

    # Shutdown
    try:
        mcp_client = MCPClient()
        if mcp_client:
            await mcp_client.cleanup()
        logger.info("MCP client closed successfully")
    except Exception as e:
        logger.error(f"Error closing MCP client: {str(e)}")

    logger.info("Shutting down COMPASS AI Service")

app = FastAPI(
    title="COMPASS AI Service",
    description="AI Service for COMPASS platform",
    version="1.0.0",
    lifespan=lifespan
)

# Mount API routes
app.include_router(ai_router)

if __name__ == "__main__":
    uvicorn.run(
        "Backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

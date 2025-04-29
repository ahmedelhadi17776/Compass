from fastapi import FastAPI
from contextlib import asynccontextmanager
from Backend.api.ai_routes import router as ai_router
from Backend.mcp.server import setup_mcp_server
from Backend.core.config import settings
import uvicorn
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("Starting up COMPASS AI Service")
    try:
        mcp = setup_mcp_server(app)
        if mcp:
            logger.info("MCP server initialized successfully")
        else:
            logger.warning("MCP server initialization failed")
    except Exception as e:
        logger.error(f"Error initializing MCP server: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down COMPASS AI Service")

app = FastAPI(
    title="COMPASS AI Service",
    description="AI Service for COMPASS platform",
    version="1.0.0",
    lifespan=lifespan
)

# Mount traditional REST endpoints
app.include_router(ai_router)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )

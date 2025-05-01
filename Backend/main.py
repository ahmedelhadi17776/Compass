from fastapi import FastAPI
from contextlib import asynccontextmanager
from Backend.api.ai_routes import router as ai_router
from Backend.core.config import settings
from Backend.mcp_py.client import MCPClient
from Backend.core.mcp_state import set_mcp_client
from Backend.mcp_py.server import setup_mcp_server
import uvicorn
import logging
import subprocess
import os
import sys

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("Starting up COMPASS AI Service")
    mcp_process = None
    mcp_client = None

    try:
        # Start Python MCP server in background
        logger.info("Starting MCP server...")

        # Get the absolute path to the Backend directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        server_path = os.path.join(backend_dir, "mcp_py", "server.py")

        # Set up environment with correct PYTHONPATH
        env = os.environ.copy()
        parent_dir = os.path.dirname(backend_dir)
        env["PYTHONPATH"] = parent_dir

        logger.info(f"Starting MCP server at: {server_path}")
        logger.info(f"With PYTHONPATH: {env['PYTHONPATH']}")

        mcp_process = subprocess.Popen(
            [sys.executable, server_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            universal_newlines=True,
            cwd=parent_dir,
            env=env
        )
        logger.info("MCP server started")

        # Initialize MCP client
        mcp_client = MCPClient()
        await mcp_client.connect_to_server(server_path)
        set_mcp_client(mcp_client)
        logger.info("MCP client initialized successfully")

        # Setup MCP server routes
        setup_mcp_server(app)
        logger.info("MCP server routes initialized")

        # Initialize any other startup services here
        logger.info("AI Service initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        if mcp_process:
            mcp_process.terminate()
        raise

    yield

    # Shutdown
    try:
        if mcp_client:
            await mcp_client.cleanup()
            logger.info("MCP client closed successfully")

        if mcp_process:
            mcp_process.terminate()
            mcp_process.wait(timeout=5)
            logger.info("MCP server stopped successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

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

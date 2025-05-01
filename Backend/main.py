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
import asyncio
import threading

logger = logging.getLogger(__name__)

# Set Windows-compatible event loop policy at the module level
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logger.info("Set Windows-compatible event loop policy")


def run_mcp_server_subprocess(server_path, env):
    """Run the MCP server as a subprocess in a thread-safe way."""
    try:
        # For Windows, use a different approach that doesn't rely on asyncio's subprocess handling
        if sys.platform == "win32":
            # Start the process detached from the parent process
            process = subprocess.Popen(
                [sys.executable, server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                universal_newlines=True,
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
        else:
            # For non-Windows platforms, use the original approach
            process = subprocess.Popen(
                [sys.executable, server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                universal_newlines=True,
                env=env
            )
            
        logger.info(f"Started MCP server process with PID: {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Failed to start MCP server process: {str(e)}")
        return None


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

        # Use the dedicated function to start the server subprocess
        mcp_process = run_mcp_server_subprocess(server_path, env)

        if not mcp_process:
            logger.error("Failed to start MCP server process")
            raise RuntimeError("Failed to start MCP server")

        logger.info("MCP server started")

        # Wait a moment for the server to initialize
        await asyncio.sleep(1)

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
            if sys.platform == "win32":
                # On Windows, we need to use taskkill to terminate the process
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(mcp_process.pid)])
                except Exception as kill_error:
                    logger.error(
                        f"Error terminating MCP process: {str(kill_error)}")
            else:
                mcp_process.terminate()
        raise

    yield

    # Shutdown
    try:
        if mcp_client:
            await mcp_client.cleanup()
            logger.info("MCP client closed successfully")

        if mcp_process:
            if sys.platform == "win32":
                # On Windows, we need to use taskkill to terminate the process
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(mcp_process.pid)])
                except Exception as e:
                    logger.error(f"Error terminating MCP process: {str(e)}")
            else:
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

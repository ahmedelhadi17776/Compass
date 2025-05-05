import os
import sys
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Depends, Cookie, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import pathlib

# Import the API routers directly
from api.ai_routes import router as ai_router
from core.mcp_state import set_mcp_client, get_mcp_client
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('compass.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize MCP client in lifespan context


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and manage resources."""
    try:
        # Initialize the MCP server if enabled
        if settings.mcp_enabled:
            await init_mcp_server()

        logger.info("Application started successfully")
        yield
    finally:
        # Cleanup MCP client when app shuts down
        logger.info("Shutting down application...")
        if settings.mcp_enabled:
            await cleanup_mcp()
        logger.info("All resources cleaned up")

# Create FastAPI app with lifespan
app = FastAPI(title="COMPASS Backend", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(ai_router)

# Mount static files directory only if it exists
static_dir = pathlib.Path("static")
if static_dir.exists() and static_dir.is_dir():
    logger.info(f"Mounting static files directory: {static_dir}")
    app.mount("/static", StaticFiles(directory="static"), name="static")
else:
    logger.warning(
        f"Static directory '{static_dir}' does not exist - not mounting static files")
    # Create the directory to prevent future errors if needed
    try:
        static_dir.mkdir(exist_ok=True)
        logger.info(f"Created static directory: {static_dir}")
    except Exception as e:
        logger.warning(f"Could not create static directory: {str(e)}")


async def init_mcp_server():
    """Initialize MCP server integration."""
    logger.info("Initializing MCP server integration")

    try:
        # Import MCP client and server
        from mcp_py.client import MCPClient
        from mcp_py.server import run_server

        # Start the MCP server in the background
        server_script_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "mcp_py", "server.py"))

        # Validate the server script path
        if not os.path.exists(server_script_path):
            logger.error(
                f"MCP server script not found at {server_script_path}")
            return

        logger.info(f"Starting MCP server: {server_script_path}")

        # Start the MCP server on a separate process
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            server_script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy()
        )

        # Wait for the server to start
        server_init_wait = 3.0  # Seconds to wait for server initialization
        logger.info(
            f"Waiting {server_init_wait} seconds for MCP server to initialize...")
        await asyncio.sleep(server_init_wait)

        # Check if process is still running
        if process.returncode is not None:
            stdout, stderr = await process.communicate()
            logger.error(
                f"MCP server failed to start. Return code: {process.returncode}")
            logger.error(f"STDOUT: {stdout.decode()}")
            logger.error(f"STDERR: {stderr.decode()}")
            return

        # Create and configure MCP client
        logger.info("Initializing MCP client")
        mcp_client = MCPClient()

        # Connect to the server with retry logic
        await mcp_client.connect_to_server(server_script_path, max_retries=3, retry_delay=2.0)

        # Store the MCP client in the global state
        set_mcp_client(mcp_client)

        # Wait for tools to be registered and check
        await asyncio.sleep(1.0)
        tools = await mcp_client.get_tools()
        if tools:
            logger.info(f"MCP client initialized with {len(tools)} tools")
        else:
            logger.warning(
                "MCP client initialized but no tools were registered")

        logger.info("MCP server integration complete")

    except Exception as e:
        logger.error(f"Error initializing MCP server: {str(e)}", exc_info=True)


async def cleanup_mcp():
    """Cleanup MCP client resources."""
    try:
        logger.info("Cleaning up MCP resources")
        mcp_client = get_mcp_client()
        if mcp_client:
            await mcp_client.cleanup()
            logger.info("MCP client resources cleaned up successfully")
        else:
            logger.info("No MCP client to clean up")
    except Exception as e:
        logger.error(f"Error during MCP cleanup: {str(e)}", exc_info=True)

# Root endpoint


@app.get("/")
async def root():
    return {"message": "Welcome to COMPASS Backend", "version": "1.0.0"}

# Health check endpoint


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

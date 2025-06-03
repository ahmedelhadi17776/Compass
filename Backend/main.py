from data_layer.mongodb.lifecycle import mongodb_lifespan
from data_layer.mongodb.connection import get_mongodb_client
from core.config import settings
from core.mcp_state import set_mcp_client, get_mcp_client
from api.ai_routes import router as ai_router
from data_layer.cache.redis_client import redis_client
import pathlib
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi import FastAPI, Request, Depends, Cookie, HTTPException
from typing import Dict, Any, Optional
import logging
import json
import asyncio
import os
import sys
import codecs
import datetime
import io
from api.focus_routes import router as focus_router

# Set up proper encoding for stdout/stderr
try:
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
except (AttributeError, IOError):
    pass


class EmojiSafeFormatter(logging.Formatter):
    """Log formatter that makes emojis and special characters safe for console output."""

    def format(self, record):
        msg = super().format(record)
        # Replace common emojis with text equivalents
        replacements = {
            '✅': '[OK]',
            '❌': '[X]',
            '⚠️': '[WARN]',
            '🔄': '[REFRESH]',
            '🚀': '[ROCKET]',
            '📊': '[CHART]',
            '🔍': '[SEARCH]',
            '🔒': '[LOCK]'
        }

        for emoji, replacement in replacements.items():
            msg = msg.replace(emoji, replacement)
        return msg

# Configure logging with Unicode safety


class EncodingSafeHandler(logging.StreamHandler):
    """Stream handler that handles encoding errors gracefully."""

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Use a safer approach to write to the stream
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            # Fall back to ascii with replacement if Unicode fails
            try:
                msg = self.format(record)
                # Replace problematic characters
                safe_msg = msg.encode('ascii', 'replace').decode('ascii')
                stream = self.stream
                stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)
        except Exception:
            self.handleError(record)


# Configure the root logger
logger_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = EmojiSafeFormatter(logger_format)

# Clear any existing handlers
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Add new safe handlers
console_handler = EncodingSafeHandler(sys.stdout)
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler('compass.log', encoding='utf-8')
file_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)

logger = logging.getLogger(__name__)
logger.info("Logging initialized with emoji-safe configuration")

# Combine multiple lifecycle managers using nested context managers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and manage resources using multiple lifecycle managers."""
    try:
        # Initialize Redis
        logger.info("Testing Redis connection...")
        try:
            # Ping Redis on database 1
            await redis_client.ping()
            logger.info("✅ Redis connection successful on database 1")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {str(e)}")
            raise

        # Pre-load sentence transformer model
        logger.info("Pre-loading sentence transformer model...")
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            app.state.sentence_transformer = model
            logger.info("✅ Sentence transformer model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load sentence transformer: {str(e)}")
            raise

        # Initialize MongoDB
        async with mongodb_lifespan(app):
            # Initialize the MCP server if enabled
            if settings.mcp_enabled:
                await init_mcp_server()

            logger.info("Application started successfully")
            yield
    finally:
        # Cleanup resources when app shuts down
        logger.info("Shutting down application...")
        if settings.mcp_enabled:
            result = await cleanup_mcp()

        # Close Redis connection
        try:
            await redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")

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
app.include_router(focus_router)

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

        # Wait for the server to start - increased wait time for better initialization
        server_init_wait = 5.0
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

        # Connect to the server with retry logic and increased retry delay
        await mcp_client.connect_to_server(server_script_path, max_retries=5, retry_delay=3.0)

        # Store the MCP client in the global state
        set_mcp_client(mcp_client)

        # Wait longer for tools to be registered - increased from 1.0 to 5.0 seconds
        logger.info("Waiting for tools to be registered...")
        await asyncio.sleep(5.0)

        # Try multiple times to get tools if not available on first attempt
        max_tool_attempts = 3
        for attempt in range(max_tool_attempts):
            tools = await mcp_client.get_tools()
            if tools:
                logger.info(f"MCP client initialized with {len(tools)} tools")
                break
            elif attempt < max_tool_attempts - 1:
                logger.warning(
                    f"No tools found on attempt {attempt+1}, waiting before retry...")
                await asyncio.sleep(2.0)
            else:
                logger.warning(
                    "MCP client initialized but no tools were registered after multiple attempts")

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
        return True  # Return a value to ensure it's awaitable
    except Exception as e:
        logger.error(f"Error during MCP cleanup: {str(e)}", exc_info=True)
        return False  # Return a value even in case of error

# Root endpoint


@app.get("/")
async def root():
    return {"message": "Welcome to COMPASS Backend", "version": "1.0.0"}

# Health check endpoint


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker healthcheck."""
    try:
        # Check MongoDB connection
        client = get_mongodb_client()
        db = client.admin
        server_info = db.command("ping")
        mongodb_ok = server_info.get("ok") == 1.0
    except Exception as e:
        logger.error(f"MongoDB health check error: {str(e)}")
        mongodb_ok = False

    # Check Redis connection
    try:
        redis_ok = await redis_client.ping()
        logger.info("Redis health check passed")
    except Exception as e:
        logger.error(f"Redis health check error: {str(e)}")
        redis_ok = False

    return {
        "status": "healthy" if (mongodb_ok and redis_ok) else "degraded",
        "mongodb": mongodb_ok,
        "redis": redis_ok,
        "redis_db": 1,  # Show which Redis DB we're using
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn

    # Check if HTTPS is enabled in settings
    if settings.use_https:
        logger.info(
            f"Starting server with HTTPS on {settings.api_host}:{settings.api_port}")
        logger.info(f"Using certificate: {settings.https_cert_file}")
        logger.info(f"Using key: {settings.https_key_file}")

        uvicorn.run(
            "main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=True,
            ssl_keyfile=settings.https_key_file,
            ssl_certfile=settings.https_cert_file
        )
    else:
        logger.info(
            f"Starting server with HTTP on {settings.api_host}:{settings.api_port}")
        uvicorn.run("main:app", host=settings.api_host,
                    port=settings.api_port, reload=True)

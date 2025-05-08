import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from data_layer.mongodb.connection import (
    get_mongodb_client,
    get_async_mongodb_client,
    close_mongodb_connections
)

logger = logging.getLogger(__name__)


async def init_mongodb():
    """Initialize MongoDB connections and verify connectivity."""
    try:
        logger.info("Initializing MongoDB connections")

        # Test sync connection
        client = get_mongodb_client()
        db = client.admin
        server_info = db.command("serverStatus")
        logger.info(
            f"Connected to MongoDB version: {server_info.get('version', 'unknown')}")

        # Test async connection
        async_client = get_async_mongodb_client()
        logger.info("Initialized async MongoDB client")

        return True
    except Exception as e:
        logger.error(f"Error initializing MongoDB: {str(e)}")
        return False


@asynccontextmanager
async def mongodb_lifespan(app: FastAPI):
    """Lifespan manager for MongoDB connections."""
    # Initialize MongoDB on startup
    mongodb_ok = await init_mongodb()
    if mongodb_ok:
        logger.info("MongoDB integration ready")
    else:
        logger.warning(
            "MongoDB integration failed - some features may not work")

    yield

    # Close connections on shutdown
    await close_mongodb_connections()
    logger.info("MongoDB connections closed")

from typing import Optional, Dict, Any, List, cast, TYPE_CHECKING
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from functools import lru_cache
from core.config import settings

logger = logging.getLogger(__name__)

# Singleton MongoDB client - use Any for global variables to avoid type errors
_mongodb_client: Any = None
_async_mongodb_client: Any = None


@lru_cache(maxsize=1)
def get_mongodb_uri() -> str:
    """Get MongoDB URI from settings or environment variables."""
    # Use settings first, with fallback to explicit connection parameters
    if hasattr(settings, 'mongodb_uri') and settings.mongodb_uri:
        return settings.mongodb_uri

    # Construct URI from individual components
    host = settings.mongodb_host if hasattr(
        settings, 'mongodb_host') else "localhost"
    port = settings.mongodb_port if hasattr(
        settings, 'mongodb_port') else 27017
    username = getattr(settings, 'mongodb_username', "")
    password = getattr(settings, 'mongodb_password', "")

    # Build connection string
    if username and password:
        return f"mongodb://{username}:{password}@{host}:{port}"
    return f"mongodb://{host}:{port}"


def get_mongodb_client() -> Any:
    """Get MongoDB client singleton with connection pooling."""
    global _mongodb_client

    if _mongodb_client is None:
        uri = get_mongodb_uri()
        logger.info(f"Connecting to MongoDB at {uri.split('@')[-1]}")

        try:
            # Configure client with connection pooling and timeouts
            _mongodb_client = MongoClient(
                uri,
                maxPoolSize=50,  # Maximum number of connections in the pool
                minPoolSize=10,   # Minimum number of connections in the pool
                # Max idle time for a connection (30 seconds)
                maxIdleTimeMS=30000,
                connectTimeoutMS=5000,  # Connection timeout (5 seconds)
                # Server selection timeout (5 seconds)
                serverSelectionTimeoutMS=5000,
                retryWrites=True,  # Enable retryable writes
                w='majority'  # Write concern for data durability
            )

            # Test connection
            _mongodb_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    return _mongodb_client


def get_async_mongodb_client() -> Any:
    """Get async MongoDB client singleton."""
    global _async_mongodb_client

    if _async_mongodb_client is None:
        uri = get_mongodb_uri()
        logger.info(f"Connecting to MongoDB (async) at {uri.split('@')[-1]}")

        try:
            # Configure async client
            _async_mongodb_client = AsyncIOMotorClient(
                uri,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
                retryWrites=True,
                w='majority'
            )
            logger.info("Successfully created async MongoDB client")
        except Exception as e:
            logger.error(f"Failed to create async MongoDB client: {e}")
            raise

    return _async_mongodb_client


def get_database(db_name: Optional[str] = None) -> Database:
    """Get MongoDB database."""
    client = get_mongodb_client()
    database_name = db_name or getattr(settings, 'mongodb_database', 'compass')
    return client[database_name]


def get_async_database(db_name: Optional[str] = None) -> Any:
    """Get async MongoDB database."""
    client = get_async_mongodb_client()
    database_name = db_name or getattr(settings, 'mongodb_database', 'compass')
    return client[database_name]


def get_collection(collection_name: str, db_name: Optional[str] = None) -> Collection:
    """Get MongoDB collection."""
    db = get_database(db_name)
    return db[collection_name]


def get_async_collection(collection_name: str, db_name: Optional[str] = None) -> Any:
    """Get async MongoDB collection."""
    db = get_async_database(db_name)
    return db[collection_name]


async def close_mongodb_connections():
    """Close all MongoDB connections."""
    global _mongodb_client, _async_mongodb_client

    logger.info("Closing MongoDB connections")

    if _mongodb_client is not None:
        _mongodb_client.close()
        _mongodb_client = None
        logger.info("Closed sync MongoDB client")

    if _async_mongodb_client is not None:
        _async_mongodb_client.close()
        _async_mongodb_client = None
        logger.info("Closed async MongoDB client")

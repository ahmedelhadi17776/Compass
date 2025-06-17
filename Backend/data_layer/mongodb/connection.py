from typing import Optional, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from functools import lru_cache
from core.config import settings

logger = logging.getLogger(__name__)

# Singleton MongoDB client - use Any for global variables to avoid type errors
_mongodb_client: Any = None
_async_mongodb_client: Any = None

# Connection pool settings from core.config
MAX_POOL_SIZE = settings.mongodb_max_pool_size
MIN_POOL_SIZE = settings.mongodb_min_pool_size
MAX_IDLE_TIME_MS = settings.mongodb_max_idle_time_ms
CONNECT_TIMEOUT_MS = settings.mongodb_connect_timeout_ms
SERVER_SELECTION_TIMEOUT_MS = settings.mongodb_server_selection_timeout_ms
MAX_CONNECTING = settings.mongodb_max_connecting
WAIT_QUEUE_TIMEOUT_MS = settings.mongodb_wait_queue_timeout_ms


@lru_cache(maxsize=1)
def get_mongodb_uri() -> str:
    """Get MongoDB URI from settings or environment variables."""
    return settings.mongodb_uri


def get_mongodb_client() -> Any:
    """Get MongoDB client singleton with optimized connection pooling."""
    global _mongodb_client

    if _mongodb_client is None:
        uri = get_mongodb_uri()
        logger.info(f"Connecting to MongoDB at {uri.split('@')[-1]}")

        try:
            # Configure client with enhanced connection pooling and timeouts
            _mongodb_client = MongoClient(
                uri,
                maxPoolSize=MAX_POOL_SIZE,
                minPoolSize=MIN_POOL_SIZE,
                maxIdleTimeMS=MAX_IDLE_TIME_MS,
                connectTimeoutMS=CONNECT_TIMEOUT_MS,
                serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS,
                retryWrites=True,  # Enable retryable writes
                w='majority',  # Write concern for data durability
                maxConnecting=MAX_CONNECTING,  # Limit concurrent connection establishments
                # How long operations wait for a connection
                waitQueueTimeoutMS=WAIT_QUEUE_TIMEOUT_MS
            )

            # Test connection
            _mongodb_client.admin.command('ping')
            logger.info(
                f"Successfully connected to MongoDB with pool size: {MAX_POOL_SIZE}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    return _mongodb_client


def get_async_mongodb_client() -> Any:
    """Get async MongoDB client singleton with optimized connection pooling."""
    global _async_mongodb_client

    if _async_mongodb_client is None:
        uri = get_mongodb_uri()
        logger.info(f"Connecting to MongoDB (async) at {uri.split('@')[-1]}")

        try:
            # Configure async client with enhanced connection pooling
            _async_mongodb_client = AsyncIOMotorClient(
                uri,
                maxPoolSize=MAX_POOL_SIZE,
                minPoolSize=MIN_POOL_SIZE,
                maxIdleTimeMS=MAX_IDLE_TIME_MS,
                connectTimeoutMS=CONNECT_TIMEOUT_MS,
                serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS,
                retryWrites=True,
                w='majority',
                maxConnecting=MAX_CONNECTING,
                waitQueueTimeoutMS=WAIT_QUEUE_TIMEOUT_MS
            )
            logger.info(
                f"Successfully created async MongoDB client with pool size: {MAX_POOL_SIZE}")
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

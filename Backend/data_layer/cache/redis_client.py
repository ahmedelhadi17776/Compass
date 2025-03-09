import redis.asyncio as redis
from Backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

# ✅ Initialize Redis Connection
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_cached_value(key: str):
    """Retrieve a cached value from Redis."""
    return await redis_client.get(key)


async def set_cached_value(key: str, value: str, ttl: int = 3600):
    """Store a value in Redis with a time-to-live (TTL)."""
    await redis_client.setex(key, ttl, value)


async def delete_cached_value(key: str):
    """
    Delete a cached value from Redis.
    If the key contains a wildcard (*), it will delete all matching keys.
    """
    if '*' in key:
        # Pattern deletion - scan and delete matching keys
        cursor = 0
        deleted_count = 0
        while True:
            cursor, keys = await redis_client.scan(cursor, match=key, count=100)
            if keys:
                deleted_count += await redis_client.delete(*keys)
            if cursor == 0:
                break
        logger.debug(f"Deleted {deleted_count} keys matching pattern: {key}")
        return deleted_count
    else:
        # Single key deletion
        return await redis_client.delete(key)

import redis.asyncio as redis
from core.config import settings

# ✅ Initialize Redis Connection
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_cached_value(key: str):
    """Retrieve a cached value from Redis."""
    return await redis_client.get(key)


async def set_cached_value(key: str, value: str, ttl: int = 3600):
    """Store a value in Redis with a time-to-live (TTL)."""
    await redis_client.setex(key, ttl, value)


async def delete_cached_value(key: str):
    """Delete a cached value from Redis."""
    await redis_client.delete(key)

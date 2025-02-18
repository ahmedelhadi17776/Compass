import json
from typing import Any, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from functools import wraps
import hashlib
import pickle


class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(
            redis_url, encoding="utf-8", decode_responses=True)

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        nx: bool = False
    ) -> bool:
        """
        Set key-value pair in Redis.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
            nx: If True, set only if key doesn't exist
        """
        try:
            # Serialize value if it's not a string
            if not isinstance(value, (str, int, float)):
                value = json.dumps(value)

            if nx:
                return await self.redis.set(key, value, ex=expire, nx=True)
            return await self.redis.set(key, value, ex=expire)
        except Exception as e:
            print(f"Error setting cache: {str(e)}")
            return False

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from Redis."""
        try:
            value = await self.redis.get(key)
            if value is None:
                return default

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Error getting from cache: {str(e)}")
            return default

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            return bool(await self.redis.delete(key))
        except Exception as e:
            print(f"Error deleting from cache: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            print(f"Error checking cache existence: {str(e)}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value in Redis."""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            print(f"Error incrementing cache: {str(e)}")
            return None

    async def expire_at(self, key: str, timestamp: Union[int, datetime]) -> bool:
        """Set expiration time for key."""
        try:
            if isinstance(timestamp, datetime):
                timestamp = int(timestamp.timestamp())
            return await self.redis.expireat(key, timestamp)
        except Exception as e:
            print(f"Error setting expiration: {str(e)}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Error clearing cache pattern: {str(e)}")
            return 0


def cache_key_builder(*args, **kwargs) -> str:
    """Build cache key from arguments."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def async_cache(
    cache: RedisCache,
    prefix: str,
    expire: Optional[int] = None,
    key_builder: callable = cache_key_builder
):
    """
    Decorator for caching async function results.

    Args:
        cache: RedisCache instance
        prefix: Cache key prefix
        expire: Cache expiration time in seconds
        key_builder: Function to build cache key from arguments
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = f"{prefix}:{key_builder(*args, **kwargs)}"

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, expire=expire)
            return result
        return wrapper
    return decorator


class LocalCache:
    """Simple in-memory cache with expiration."""

    def __init__(self):
        self._cache = {}
        self._expires = {}

    def set(self, key: str, value: Any, expire: Optional[int] = None):
        """Set value in cache with optional expiration."""
        self._cache[key] = value
        if expire:
            self._expires[key] = datetime.now() + timedelta(seconds=expire)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        self._cleanup()
        return self._cache.get(key, default)

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        self._cleanup()
        if key in self._cache:
            del self._cache[key]
            self._expires.pop(key, None)
            return True
        return False

    def _cleanup(self):
        """Remove expired entries."""
        now = datetime.now()
        expired = [
            key for key, expires in self._expires.items()
            if expires <= now
        ]
        for key in expired:
            self._cache.pop(key, None)
            self._expires.pop(key, None)

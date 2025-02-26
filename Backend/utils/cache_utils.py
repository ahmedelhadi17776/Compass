from functools import wraps
from typing import Any, Callable, Optional
import json
from datetime import datetime, timedelta
import redis
from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger

logger = get_logger(__name__)

# Initialize Redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

def generate_cache_key(func: Callable, *args, **kwargs) -> str:
    """Generate a unique cache key based on function name and arguments."""
    try:
        # Create a unique key based on function name and arguments
        key_parts = [
            func.__module__,
            func.__name__,
            str(args),
            str(sorted(kwargs.items()))
        ]
        return ":".join(key_parts)
    except Exception as e:
        logger.error(f"Error generating cache key: {str(e)}")
        return f"{func.__module__}:{func.__name__}:fallback"

def serialize_data(data: Any) -> str:
    """Serialize data to JSON string format."""
    try:
        return json.dumps(data)
    except Exception as e:
        logger.error(f"Error serializing data: {str(e)}")
        raise

def deserialize_data(data_str: str) -> Any:
    """Deserialize JSON string back to Python object."""
    try:
        return json.loads(data_str)
    except Exception as e:
        logger.error(f"Error deserializing data: {str(e)}")
        raise

def cache_response(ttl: int = 3600):
    """Decorator to cache function responses in Redis.
    
    Args:
        ttl (int): Time to live in seconds for cached data. Defaults to 1 hour.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Generate cache key
                cache_key = generate_cache_key(func, *args, **kwargs)
                
                # Try to get cached response
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return deserialize_data(cached_data)
                
                # If no cache, execute function and cache result
                result = await func(*args, **kwargs)
                serialized_result = serialize_data(result)
                
                # Store in Redis with TTL
                redis_client.setex(cache_key, ttl, serialized_result)
                
                return result
            except redis.RedisError as e:
                logger.error(f"Redis error in cache_response: {str(e)}")
                # Fall back to executing function without caching
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Unexpected error in cache_response: {str(e)}")
                raise
        
        return wrapper
    return decorator

def clear_cache(pattern: str = "*") -> None:
    """Clear cache entries matching the given pattern.
    
    Args:
        pattern (str): Pattern to match cache keys. Defaults to all keys.
    """
    try:
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match=pattern)
            if keys:
                redis_client.delete(*keys)
            if cursor == 0:
                break
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise

def get_cache_stats() -> dict:
    """Get cache statistics and metrics."""
    try:
        info = redis_client.info()
        return {
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_keys": redis_client.dbsize(),
            "uptime_days": info.get("uptime_in_days")
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise

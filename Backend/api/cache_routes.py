from fastapi import APIRouter, Depends
from Backend.utils.cache_utils import get_cache_stats
from Backend.data_layer.cache.redis_client import get_cached_value, set_cached_value
import json

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats")
async def cache_stats():
    """Returns Redis cache statistics and metrics."""
    return await get_cache_stats_with_cache()


async def get_cache_stats_with_cache():
    """Get cache statistics with caching for 30 seconds."""
    cache_key = "cache_stats"
    
    # Check if cached value exists
    cached_response = await get_cached_value(cache_key)
    if cached_response:
        return json.loads(cached_response)
    
    # If no cache, get fresh stats
    stats = get_cache_stats()
    
    # Cache for 30 seconds
    await set_cached_value(cache_key, json.dumps(stats), ttl=30)
    
    return stats
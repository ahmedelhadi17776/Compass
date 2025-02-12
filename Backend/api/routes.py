from fastapi import APIRouter, Depends
from data_layer.cache.redis_client import get_cached_value, set_cached_value
import json

router = APIRouter()


@router.get("/ping")
async def ping():
    """
    Simple health check endpoint.
    """
    return {"message": "pong"}


@router.get("/status")
async def status():
    """
    Returns API status.
    """
    return {"status": "running"}


@router.get("/cached-status")
async def cached_status():
    """Returns API status with Redis caching."""
    cache_key = "api_status"

    # ✅ Check if cached value exists
    cached_response = await get_cached_value(cache_key)
    if cached_response:
        return json.loads(cached_response)  # Return cached response

    # ✅ If no cache, generate response and store in Redis
    response = {"status": "running", "message": "API is working!"}
    # Cache for 60 sec
    await set_cached_value(cache_key, json.dumps(response), ttl=60)

    return response

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from data_layer.cache.dashboard_cache import dashboard_cache
from utils.jwt import extract_user_id_from_token
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/dashboard/metrics')
async def get_dashboard_metrics(
    request: Request,
    user_id: str = Depends(extract_user_id_from_token),
    authorization: Optional[str] = Header(None)
):
    # Extract token from authorization header if present
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")

    logger.debug(f"Fetching dashboard metrics for user {user_id}")
    metrics = await dashboard_cache.get_metrics(user_id, token)
    return JSONResponse(content=metrics)

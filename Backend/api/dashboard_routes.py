from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from data_layer.cache.dashboard_cache import dashboard_cache
from utils.jwt import extract_user_id_from_token

router = APIRouter()


@router.get('/dashboard/metrics')
async def get_dashboard_metrics(user_id: str = Depends(extract_user_id_from_token)):
    metrics = await dashboard_cache.get_metrics(user_id)
    return JSONResponse(content=metrics)

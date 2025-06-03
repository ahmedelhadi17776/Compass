from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict
from app.schemas.system_metric_schemas import SystemMetricCreate, SystemMetricResponse, SystemMetricListResponse
from data_layer.repos.system_metric_repo import SystemMetricRepository
from data_layer.models.system_metric_model import SystemMetric
from utils.jwt import extract_user_id_from_token
from datetime import datetime
import json

router = APIRouter(prefix="/system-metrics", tags=["System Metrics"])
metric_repo = SystemMetricRepository()

# In-memory store for active dashboard WebSocket connections per user
active_dashboard_connections: Dict[str, List[WebSocket]] = {}


@router.post("/", response_model=SystemMetricResponse)
def create_metric(metric: SystemMetricCreate, user_id: str = Depends(extract_user_id_from_token)):
    metric_data = metric.dict()
    metric_data["user_id"] = user_id
    if not metric_data.get("timestamp"):
        metric_data["timestamp"] = datetime.utcnow()
    metric_obj = SystemMetric(**metric_data)
    metric_id = metric_repo.create_metric(metric_obj)
    return SystemMetricResponse(id=str(metric_id), user_id=user_id, **metric.dict())


@router.get("/", response_model=SystemMetricListResponse)
def list_metrics(user_id: str = Depends(extract_user_id_from_token)):
    metrics = metric_repo.find_by_user(user_id)
    return SystemMetricListResponse(metrics=[SystemMetricResponse(id=str(m.id), user_id=m.user_id, metric_type=m.metric_type, value=m.value, timestamp=m.timestamp, metadata=m.metadata) for m in metrics])


@router.get("/range", response_model=SystemMetricListResponse)
def metrics_by_type_and_range(
    metric_type: str = Query(...),
    start: datetime = Query(...),
    end: datetime = Query(...),
    user_id: str = Depends(extract_user_id_from_token)
):
    metrics = metric_repo.find_by_type_and_range(
        user_id, metric_type, start, end)
    return SystemMetricListResponse(metrics=[SystemMetricResponse(id=str(m.id), user_id=m.user_id, metric_type=m.metric_type, value=m.value, timestamp=m.timestamp, metadata=m.metadata) for m in metrics])


@router.websocket("/ws")
async def system_metrics_ws(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    try:
        # Expect JWT in query params or headers
        token = websocket.headers.get("authorization")
        if not token:
            await websocket.close(code=4001)
            return
        user_id = extract_user_id_from_token(token)
        # Register this connection for dashboard updates
        if user_id not in active_dashboard_connections:
            active_dashboard_connections[user_id] = []
        active_dashboard_connections[user_id].append(websocket)
        while True:
            data = await websocket.receive_text()
            metric_data = json.loads(data)
            metric_data["user_id"] = user_id
            if not metric_data.get("timestamp"):
                metric_data["timestamp"] = datetime.utcnow().isoformat()
            metric = SystemMetric(**metric_data)
            metric_repo.create_metric(metric)
            # Broadcast to all dashboard clients for this user
            for ws in active_dashboard_connections.get(user_id, []):
                if ws != websocket:
                    try:
                        await ws.send_text(json.dumps({"event": "system_metric", "data": metric_data}))
                    except Exception:
                        pass
    except WebSocketDisconnect:
        if user_id and user_id in active_dashboard_connections:
            active_dashboard_connections[user_id].remove(websocket)
            if not active_dashboard_connections[user_id]:
                del active_dashboard_connections[user_id]
    except Exception:
        if websocket.client_state.value == 1:  # OPEN
            await websocket.close(code=4002)


@router.get("/summary", response_model=List[Dict])
def summary_metrics(
    period: str = Query(
        "daily", description="Aggregation period: daily, weekly, monthly"),
    metric_type: Optional[str] = Query(
        None, description="Metric type to filter (optional)"),
    start: Optional[datetime] = Query(
        None, description="Start datetime (optional)"),
    end: Optional[datetime] = Query(
        None, description="End datetime (optional)"),
    user_id: str = Depends(extract_user_id_from_token)
):
    """
    Get aggregated system metrics for the dashboard. Returns sum, avg, min, max, count per period and metric_type.
    """
    results = metric_repo.aggregate_metrics(
        user_id, period=period, metric_type=metric_type, start=start, end=end)
    return results

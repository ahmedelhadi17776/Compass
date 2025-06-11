from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from data_layer.repos.focus_repo import FocusSessionRepository
from app.schemas.focus_schemas import FocusSessionCreate, FocusSessionStop, FocusSessionResponse, FocusStatsResponse
from utils.jwt import extract_user_id_from_token
from data_layer.models.focus_model import FocusSession
from typing import List, Dict
from datetime import timezone
import asyncio
from fastapi.encoders import jsonable_encoder
from data_layer.cache.pubsub_manager import pubsub_manager

router = APIRouter(prefix="/focus", tags=["Focus"])
repo = FocusSessionRepository()

# In-memory store for active dashboard WebSocket connections per user
active_focus_ws_connections: Dict[str, List[WebSocket]] = {}


@router.post("/start", response_model=FocusSessionResponse)
async def start_focus_session(data: FocusSessionCreate, user_id: str = Depends(extract_user_id_from_token)):
    active = repo.find_active_session(user_id)
    if active:
        raise HTTPException(
            status_code=400, detail="Focus session already active")
    session_obj = FocusSession(
        user_id=user_id,
        **data.model_dump(),
        end_time=None,
        duration=None,
        status="active",
        interruptions=0,
        metadata={}
    )
    inserted_id = repo.insert(session_obj)
    session = repo.find_by_id(inserted_id)
    if not session:
        raise HTTPException(
            status_code=500, detail="Failed to create focus session")
    response = FocusSessionResponse(**session.model_dump())
    # Publish to Redis pub/sub for real-time update
    serializable_response = jsonable_encoder(response.model_dump())
    await pubsub_manager.publish(user_id, "focus_session_started", serializable_response)
    stats = repo.get_stats(user_id)
    serializable_stats = jsonable_encoder(stats)
    await pubsub_manager.publish(user_id, "focus_stats", serializable_stats)
    return response


@router.post("/stop", response_model=FocusSessionResponse)
async def stop_focus_session(data: FocusSessionStop, user_id: str = Depends(extract_user_id_from_token)):
    active = repo.find_active_session(user_id)
    if not active or not active.id:
        raise HTTPException(status_code=404, detail="No active session")
    # Ensure both datetimes are timezone-aware and in UTC
    end_time_utc = data.end_time.astimezone(timezone.utc)
    start_time_utc = active.start_time
    if start_time_utc.tzinfo is None:
        start_time_utc = start_time_utc.replace(tzinfo=timezone.utc)
    duration = int((end_time_utc - start_time_utc).total_seconds())
    updated = repo.update(
        active.id,
        {
            "end_time": end_time_utc,
            "duration": duration,
            "status": "completed",
            "notes": data.notes
        }
    )
    if not updated:
        raise HTTPException(
            status_code=500, detail="Failed to update focus session")
    response = FocusSessionResponse(**updated.model_dump())
    # Publish to Redis pub/sub for real-time update
    serializable_response = jsonable_encoder(response.model_dump())
    await pubsub_manager.publish(user_id, "focus_session_stopped", serializable_response)
    stats = repo.get_stats(user_id)
    serializable_stats = jsonable_encoder(stats)
    await pubsub_manager.publish(user_id, "focus_stats", serializable_stats)
    return response


@router.get("/sessions", response_model=List[FocusSessionResponse])
def list_sessions(user_id: str = Depends(extract_user_id_from_token)):
    sessions = repo.find_by_user(user_id)
    return [FocusSessionResponse(**s.model_dump()) for s in sessions]


@router.get("/stats", response_model=FocusStatsResponse)
def get_stats(user_id: str = Depends(extract_user_id_from_token)):
    stats = repo.get_stats(user_id)
    return FocusStatsResponse(**stats)


@router.websocket("/ws")
async def focus_ws(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    pubsub_task = None
    try:
        token = websocket.headers.get("authorization")
        if not token:
            await websocket.close(code=4001)
            return
        user_id = extract_user_id_from_token(token)
        # Subscribe to Redis pub/sub for this user

        async def ws_callback(message):
            await websocket.send_text(message)
        await pubsub_manager.subscribe(user_id, ws_callback)
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(data)
    except WebSocketDisconnect:
        if user_id:
            await pubsub_manager.unsubscribe(user_id)
    except Exception:
        if websocket.client_state.value == 1:  # OPEN
            await websocket.close(code=4002)
        if user_id:
            await pubsub_manager.unsubscribe(user_id)

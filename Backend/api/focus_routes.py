from fastapi import APIRouter, Depends, HTTPException
from data_layer.repos.focus_repo import FocusSessionRepository
from app.schemas.focus_schemas import FocusSessionCreate, FocusSessionStop, FocusSessionResponse, FocusStatsResponse
from utils.utils import extract_user_id_from_token
from data_layer.models.focus_model import FocusSession
from typing import List
from datetime import timezone

router = APIRouter(prefix="/focus", tags=["Focus"])
repo = FocusSessionRepository()


@router.post("/start", response_model=FocusSessionResponse)
def start_focus_session(data: FocusSessionCreate, user_id: str = Depends(extract_user_id_from_token)):
    active = repo.find_active_session(user_id)
    if active:
        raise HTTPException(
            status_code=400, detail="Focus session already active")
    session_obj = FocusSession(
        user_id=user_id,
        start_time=data.start_time,
        end_time=None,
        duration=None,
        status="active",
        tags=data.tags or [],
        interruptions=0,
        notes=data.notes,
        metadata={}
    )
    inserted_id = repo.insert(session_obj)
    session = repo.find_by_id(inserted_id)
    if not session:
        raise HTTPException(
            status_code=500, detail="Failed to create focus session")
    return FocusSessionResponse(**session.model_dump())


@router.post("/stop", response_model=FocusSessionResponse)
def stop_focus_session(data: FocusSessionStop, user_id: str = Depends(extract_user_id_from_token)):
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
    return FocusSessionResponse(**updated.model_dump())


@router.get("/sessions", response_model=List[FocusSessionResponse])
def list_sessions(user_id: str = Depends(extract_user_id_from_token)):
    sessions = repo.find_by_user(user_id)
    return [FocusSessionResponse(**s.model_dump()) for s in sessions]


@router.get("/stats", response_model=FocusStatsResponse)
def get_stats(user_id: str = Depends(extract_user_id_from_token)):
    stats = repo.get_stats(user_id)
    return FocusStatsResponse(**stats)

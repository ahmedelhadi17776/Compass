from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FocusSessionCreate(BaseModel):
    start_time: datetime
    tags: Optional[List[str]] = []
    notes: Optional[str] = None


class FocusSessionStop(BaseModel):
    end_time: datetime
    notes: Optional[str] = None


class FocusSessionResponse(BaseModel):
    id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[int]
    status: str
    tags: List[str]
    interruptions: int
    notes: Optional[str]


class FocusStatsResponse(BaseModel):
    total_focus_seconds: int
    streak: int
    longest_streak: int
    sessions: int

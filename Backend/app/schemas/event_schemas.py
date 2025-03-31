from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from Backend.data_layer.database.models.calendar_event import RecurrenceType, EventType
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    duration: Optional[float] = None
    due_date: Optional[datetime] = None
    event_type: Optional[Union[EventType, str]] = EventType.NONE
    status: Union[TaskStatus, str] = TaskStatus.UPCOMING
    priority: Optional[Union[TaskPriority, str]] = None
    task_id: Optional[int] = None
    location: Optional[str] = None
    is_all_day: bool = False
    external_id: Optional[str] = None
    recurrence: Optional[Union[RecurrenceType, str]] = RecurrenceType.NONE
    recurrence_custom_days: Optional[List[str]] = None
    recurrence_end_date: Optional[datetime] = None
    recurrence_count: Optional[int] = None
    reminder_minutes_before: Optional[int] = None
    notification_method: Optional[str] = None
    time_zone: Optional[str] = None
    transparency: Optional[str] = "opaque"
    color: Optional[str] = None


class EventCreate(EventBase):
    user_id: int


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    duration: Optional[float] = None
    due_date: Optional[datetime] = None
    event_type: Optional[Union[EventType, str]] = None
    status: Optional[Union[TaskStatus, str]] = None
    priority: Optional[Union[TaskPriority, str]] = None
    task_id: Optional[int] = None
    location: Optional[str] = None
    is_all_day: Optional[bool] = None
    external_id: Optional[str] = None
    recurrence: Optional[Union[RecurrenceType, str]] = None
    recurrence_custom_days: Optional[List[str]] = None
    recurrence_end_date: Optional[datetime] = None
    recurrence_count: Optional[int] = None
    reminder_minutes_before: Optional[int] = None
    notification_method: Optional[str] = None
    modified_by_id: Optional[int] = None
    time_zone: Optional[str] = None
    transparency: Optional[str] = None
    color: Optional[str] = None

    class Config:
        orm_mode = True


class EventResponse(EventBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class MeetingNoteResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    event_id: int
    user_id: int

    class Config:
        orm_mode = True


class EventOccurrenceResponse(BaseModel):
    id: int
    calendar_event_id: int
    occurrence_num: int
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: datetime
    due_date: Optional[datetime] = None
    duration: Optional[float] = None
    status: Optional[Union[TaskStatus, str]] = None
    priority: Optional[Union[TaskPriority, str]] = None
    event_type: Optional[Union[EventType, str]] = None
    transparency: Optional[str] = None
    color: Optional[str] = None
    time_zone: Optional[str] = None
    location: Optional[str] = None
    is_all_day: Optional[bool] = None
    modified_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class EventWithDetails(EventResponse):
    meeting_notes: Optional[List[MeetingNoteResponse]] = []
    occurrences: Optional[List[EventOccurrenceResponse]] = []
    task: Optional[Dict[str, Any]] = None
    linked_todos: Optional[List[Dict[str, Any]]] = []

    class Config:
        orm_mode = True 
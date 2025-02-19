from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority

# ToDo: implemetn other necessary schemas
'''
from Backend.app.schemas.attachment_schemas import AttachmentResponse
from Backend.app.schemas.comment_schemas import CommentResponse
from Backend.app.schemas.history_schemas import HistoryResponse
'''


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    category_id: Optional[int] = None
    assignee_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    parent_task_id: Optional[int] = None


class TaskCreate(TaskBase):
    project_id: int
    organization_id: int
    workflow_id: Optional[int] = None


class TaskUpdate(TaskBase):
    status: Optional[TaskStatus] = None
    completed_at: Optional[datetime] = None
    actual_hours: Optional[float] = None
    progress_metrics: Optional[Dict] = None
    blockers: Optional[Dict] = None


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    creator_id: int
    project_id: int
    organization_id: int
    workflow_id: Optional[int]
    current_workflow_step_id: Optional[int]
    health_score: Optional[float]
    complexity_score: Optional[float]
    time_spent: Optional[int]
    progress_metrics: Optional[Dict]
    blockers: Optional[Dict]

    class Config:
        orm_mode = True


class TaskWithDetails(TaskResponse):
    attachments: List["AttachmentResponse"] = []
    comments: List["CommentResponse"] = []
    history: List["HistoryResponse"] = []
    subtasks: List["TaskResponse"] = []
    time_estimates: Optional[Dict] = None
    focus_sessions: Optional[Dict] = None
    interruption_logs: Optional[Dict] = None
    risk_factors: Optional[Dict] = None

    class Config:
        orm_mode = True


# Attachment Response Schema
class AttachmentResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_type: Optional[str]
    file_size: Optional[int]
    uploaded_by: int
    created_at: datetime

    class Config:
        orm_mode = True


# Comment Response Schema
class CommentResponse(BaseModel):
    id: int
    content: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    parent_id: Optional[int]

    class Config:
        orm_mode = True


# History Response Schema
class HistoryResponse(BaseModel):
    id: int
    action: str
    field: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

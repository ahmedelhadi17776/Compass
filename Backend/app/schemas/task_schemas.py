from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from Backend.data_layer.database.models.task import TaskStatus

# ToDo: implemetn other necessary schemas 
'''
from Backend.app.schemas.attachment_schemas import AttachmentResponse
from Backend.app.schemas.comment_schemas import CommentResponse
from Backend.app.schemas.history_schemas import HistoryResponse
'''

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = None
    category_id: Optional[int] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    project_id: int


class TaskUpdate(TaskBase):
    status: Optional[TaskStatus] = None
    completed_at: Optional[datetime] = None


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    creator_id: int
    project_id: int
    organization_id: int

    class Config:
        orm_mode = True


class TaskWithDetails(TaskResponse):
    attachments: List["AttachmentResponse"] = []
    comments: List["CommentResponse"] = []
    history: List["HistoryResponse"] = []

    class Config:
        orm_mode = True

from pydantic import BaseModel, Field
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
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    project_id: int
    organization_id: int
    workflow_id: Optional[int] = None
    assignee_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    category_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    estimated_hours: Optional[float] = None
    due_date: Optional[datetime] = None
    dependencies: Optional[List[int]] = Field(default_factory=list)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    assignee_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    priority: Optional[TaskPriority] = None
    category_id: Optional[int] = None
    due_date: Optional[datetime] = None
    actual_hours: Optional[float] = None
    progress_metrics: Optional[Dict] = Field(default_factory=dict)
    blockers: Optional[List[str]] = Field(default_factory=list)
    dependencies: Optional[List[int]] = Field(default_factory=list)
    _dependencies_list: Optional[str] = None

    class Config:
        orm_mode = True


class TaskDependencyUpdate(BaseModel):
    dependencies: List[int] = Field(default_factory=list)


class TaskResponse(TaskBase):
    id: int
    creator_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TaskWithDetails(TaskResponse):
    comments: Optional[List[Dict]] = None
    attachments: Optional[List[Dict]] = None
    history: Optional[List[Dict]] = None
    metrics: Optional[Dict] = None

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

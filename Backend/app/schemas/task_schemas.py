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
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    project_id: int
    organization_id: int
    creator_id: int
    assignee_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    category_id: Optional[int] = None
    workflow_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    estimated_hours: Optional[float] = None
    due_date: Optional[datetime] = None
    dependencies: Optional[List[int]] = Field(default_factory=list)
    
    # AI and Analytics Fields
    ai_suggestions: Optional[Dict] = Field(default_factory=dict)
    complexity_score: Optional[float] = None
    time_estimates: Optional[Dict] = Field(default_factory=dict)
    focus_sessions: Optional[Dict] = Field(default_factory=dict)
    interruption_logs: Optional[Dict] = Field(default_factory=dict)
    progress_metrics: Optional[Dict] = Field(default_factory=dict)
    blockers: Optional[List[str]] = Field(default_factory=list)
    health_score: Optional[float] = None
    risk_factors: Optional[Dict] = Field(default_factory=dict)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    category_id: Optional[int] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    dependencies: Optional[List[int]] = None
    progress_metrics: Optional[Dict] = None
    blockers: Optional[List[str]] = None
    health_score: Optional[float] = None
    risk_factors: Optional[Dict] = None


class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    actual_hours: Optional[float] = None
    confidence_score: Optional[float] = None

    class Config:
        from_attributes = True


class TaskDetail(TaskResponse):
    comments: List[Dict] = Field(default_factory=list)
    attachments: List[Dict] = Field(default_factory=list)
    history: List[Dict] = Field(default_factory=list)
    agent_interactions: List[Dict] = Field(default_factory=list)
    subtasks: List[Dict] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TaskMetrics(BaseModel):
    task_id: int
    performance_metrics: Dict
    time_tracking: Dict
    health_metrics: Dict
    ai_insights: Dict
    risk_assessment: Dict

    class Config:
        from_attributes = True


class TaskDependencyUpdate(BaseModel):
    dependencies: List[int] = Field(default_factory=list)


class TaskWithDetails(TaskResponse):
    comments: Optional[List[Dict]] = None
    attachments: Optional[List[Dict]] = None
    history: Optional[List[Dict]] = None
    metrics: Optional[Dict] = None
    ai_analysis: Optional[Dict] = Field(default_factory=dict)
    agent_interactions: Optional[List[Dict]] = Field(default_factory=list)
    optimization_score: Optional[float] = None
    ai_recommendations: Optional[List[Dict]] = Field(default_factory=list)
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
class TaskHistoryResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    action: str
    field: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    created_at: datetime
    is_ai_generated: Optional[bool] = False
    ai_confidence_score: Optional[float] = None
    ai_reasoning: Optional[str] = None

    class Config:
        from_attributes = True

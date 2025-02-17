from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(BaseModel):
    id: int
    name: str
    type: str
    input: Dict
    dependencies: Optional[List[int]] = Field(default_factory=list)
    timeout: Optional[int] = 3600  # Default 1 hour timeout
    retry_count: Optional[int] = 3
    priority: Optional[int] = 5


class WorkflowCreate(BaseModel):
    user_id: int
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStep]
    notify_on_completion: bool = True
    priority: Optional[int] = 5
    timeout: Optional[int] = 7200  # Default 2 hours timeout
    metadata: Optional[Dict] = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    workflow_id: int
    task_id: str
    status: str


class WorkflowStepExecute(BaseModel):
    user_id: int
    input_data: Dict
    priority: Optional[int] = 5
    timeout: Optional[int] = 3600


class AnalysisType(str, Enum):
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"
    BOTTLENECKS = "bottlenecks"
    OPTIMIZATION = "optimization"
    TRENDS = "trends"


class WorkflowAnalysis(BaseModel):
    user_id: int
    analysis_type: AnalysisType
    time_range: Optional[str] = None
    metrics: Optional[List[str]] = None
    options: Optional[Dict] = Field(default_factory=dict)


class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class WorkflowDetail(BaseModel):
    id: int
    name: str
    description: Optional[str]
    user_id: int
    status: WorkflowStatus
    steps: List[WorkflowStep]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    task_ids: List[str]
    metadata: Dict
    error: Optional[str]


class WorkflowStepResult(BaseModel):
    step_id: int
    task_id: str
    status: str
    result: Optional[Dict]
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class WorkflowAnalysisResult(BaseModel):
    workflow_id: int
    analysis_type: AnalysisType
    analysis_task_id: str
    insights_task_id: Optional[str]
    status: str
    results: Optional[Dict]
    created_at: datetime
    completed_at: Optional[datetime]

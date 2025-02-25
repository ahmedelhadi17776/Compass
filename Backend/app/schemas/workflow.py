from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    UNDER_REVIEW = "under_review"
    OPTIMIZING = "optimizing"


class WorkflowType(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    AI_DRIVEN = "ai_driven"
    HYBRID = "hybrid"


class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_type: WorkflowType = WorkflowType.SEQUENTIAL
    organization_id: int
    config: Optional[Dict] = Field(default_factory=dict)
    workflow_metadata: Optional[Dict] = Field(default_factory=dict)
    version: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    
    # AI Integration
    ai_enabled: bool = False
    ai_confidence_threshold: Optional[float] = None
    ai_override_rules: Optional[Dict] = Field(default_factory=dict)
    ai_learning_data: Optional[Dict] = Field(default_factory=dict)

    # Performance Configuration
    estimated_duration: Optional[int] = None
    schedule_constraints: Optional[Dict] = Field(default_factory=dict)
    error_handling_config: Optional[Dict] = Field(default_factory=dict)
    retry_policy: Optional[Dict] = Field(default_factory=dict)
    fallback_steps: Optional[Dict] = Field(default_factory=list)
    compliance_rules: Optional[Dict] = Field(default_factory=dict)
    access_control: Optional[Dict] = Field(default_factory=dict)


class WorkflowCreate(WorkflowBase):
    created_by: int
    steps: List[Dict]
    deadline: Optional[datetime] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_type: Optional[WorkflowType] = None
    config: Optional[Dict] = None
    workflow_metadata: Optional[Dict] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    ai_enabled: Optional[bool] = None
    ai_confidence_threshold: Optional[float] = None
    ai_override_rules: Optional[Dict] = None
    error_handling_config: Optional[Dict] = None
    deadline: Optional[datetime] = None


class WorkflowResponse(WorkflowBase):
    id: int
    created_by: int
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime
    last_executed_at: Optional[datetime] = None
    next_scheduled_run: Optional[datetime] = None
    
    # Performance Metrics
    average_completion_time: Optional[float] = None
    success_rate: Optional[float] = None
    optimization_score: Optional[float] = None
    bottleneck_analysis: Optional[Dict] = None
    actual_duration: Optional[int] = None
    audit_trail: Optional[Dict] = None

    class Config:
        from_attributes = True


class WorkflowDetail(WorkflowResponse):
    steps: List[Dict]
    tasks: List[Dict]
    executions: List[Dict]
    agent_interactions: List[Dict] = Field(default_factory=list)
    agent_links: List[Dict] = Field(default_factory=list)

    class Config:
        from_attributes = True


class WorkflowMetrics(BaseModel):
    workflow_id: int
    performance: Dict
    execution_stats: Dict
    timing: Dict
    ai_metrics: Dict
    bottlenecks: List[Dict] = Field(default_factory=list)
    optimization_suggestions: List[Dict] = Field(default_factory=list)

    class Config:
        from_attributes = True

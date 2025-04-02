from pydantic import BaseModel, Field, validator, conint, confloat
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


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


class StepStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class StepType(str, Enum):
    MANUAL = "manual"
    AUTOMATED = "automated"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    INTEGRATION = "integration"
    DECISION = "decision"
    AI_TASK = "ai_task"


class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    workflow_type: WorkflowType = Field(WorkflowType.SEQUENTIAL)
    organization_id: int = Field(..., gt=0)
    config: Dict[str, Any] = Field(default_factory=dict)
    workflow_metadata: Dict[str, Any] = Field(default_factory=dict)
    version: Optional[str] = Field(None, pattern=r'^\d+\.\d+\.\d+$')
    tags: List[str] = Field(default_factory=list)

    # AI Integration
    ai_enabled: bool = Field(False)
    ai_confidence_threshold: Optional[confloat(ge=0.0, le=1.0)] = Field(None)
    ai_override_rules: Dict[str, Any] = Field(default_factory=dict)
    ai_learning_data: Dict[str, Any] = Field(default_factory=dict)

    # Performance Configuration
    estimated_duration: Optional[conint(gt=0)] = Field(None)
    schedule_constraints: Dict[str, Any] = Field(default_factory=dict)
    error_handling_config: Dict[str, Any] = Field(default_factory=dict)
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    fallback_steps: List[Dict[str, Any]] = Field(default_factory=list)
    compliance_rules: Dict[str, Any] = Field(default_factory=dict)
    access_control: Dict[str, Any] = Field(default_factory=dict)

    @validator('tags')
    def validate_tags(cls, v):
        if not all(isinstance(tag, str) and tag.strip() for tag in v):
            raise ValueError('All tags must be non-empty strings')
        return [tag.strip() for tag in v]

    @validator('version')
    def validate_version(cls, v):
        if v is None:
            return v
        if not v.count('.') == 2:
            raise ValueError('Version must be in format X.Y.Z')
        return v




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
    status: Optional[WorkflowStatus] = None  # Added status field


class WorkflowStepCreate(BaseModel):
    name: str
    description: Optional[str] = None
    step_type: str  # Accept as string, will be converted to enum in repository
    step_order: Optional[int] = None
    config: Optional[Dict] = Field(default_factory=dict)
    timeout: Optional[int] = None
    is_required: bool = True
    auto_advance: bool = False
    can_revert: bool = False
    dependencies: List[int] = Field(default_factory=list)
    assigned_to: Optional[int] = None
    
    class Config:
        orm_mode = True


class WorkflowCreate(WorkflowBase):
    created_by: Optional[int] = None  # Make this optional
    creator_id: Optional[int] = None
    organization_id: Optional[int] = None  # Make this optional too
    steps: Optional[List[Dict]] = None  # Make steps optional
    deadline: Optional[datetime] = None



class WorkflowStepUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    step_type: Optional[StepType] = None
    step_order: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    is_required: Optional[bool] = None
    auto_advance: Optional[bool] = None
    can_revert: Optional[bool] = None
    timeout_seconds: Optional[int] = None
    dependencies: Optional[List[int]] = None
    assigned_to: Optional[int] = None
    notification_config: Optional[Dict[str, Any]] = None
    status: Optional[StepStatus] = None


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    workflow_type: WorkflowType
    organization_id: int
    created_by: int
    status: WorkflowStatus
    created_at: datetime
    updated_at: Optional[datetime]
    version: Optional[str]
    tags: List[str]
    ai_enabled: bool
    optimization_score: Optional[float]

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


class WorkflowDetail(BaseModel):
    id: int
    name: str
    description: str
    status: str
    workflow_type: str
    created_by: int
    organization_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    config: Dict = Field(default_factory=dict)
    ai_enabled: bool = False
    ai_confidence_threshold: Optional[float] = None
    estimated_duration: Optional[int] = None
    deadline: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    workflow_metadata: Dict = Field(default_factory=dict)
    version: str
    optimization_score: float = 0.0
    steps: List[Dict] = Field(default_factory=list)
    tasks: List[Dict] = Field(default_factory=list)
    executions: List[Dict] = Field(default_factory=list)
    
    class Config:
        orm_mode = True

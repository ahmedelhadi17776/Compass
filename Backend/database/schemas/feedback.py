"""Feedback schemas."""
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class FeedbackBase(BaseModel):
    """Base feedback schema."""

    type: str = Field(..., description="Type of feedback (bug/feature_request/improvement/general)")
    content: str = Field(..., description="Feedback content")
    category: Optional[str] = Field(None, description="Feedback category")
    context: Optional[Dict] = Field(None, description="Additional context")
    priority: str = Field("normal", description="Priority level (low/normal/high/critical)")

class FeedbackCreate(FeedbackBase):
    """Create feedback schema."""

    pass

class FeedbackUpdate(BaseModel):
    """Update feedback schema."""

    status: Optional[str] = None
    priority: Optional[str] = None
    resolution_notes: Optional[str] = None

class FeedbackComment(BaseModel):
    """Feedback comment schema."""

    id: int
    feedback_id: int
    user_id: int
    content: str
    created_at: datetime

    class Config:
        """Pydantic config."""

        orm_mode = True

class FeedbackCommentCreate(BaseModel):
    """Create feedback comment schema."""

    content: str = Field(..., description="Comment content")

class Feedback(FeedbackBase):
    """Feedback schema."""

    id: int
    user_id: int
    status: str
    resolved_by: Optional[int] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    comments: List[FeedbackComment] = []

    class Config:
        """Pydantic config."""

        orm_mode = True

class FeedbackStats(BaseModel):
    """Feedback statistics schema."""

    total: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    resolution_time_avg: float
    trending_categories: Dict[str, int]

class FeedbackExport(BaseModel):
    """Feedback export schema."""

    format: str
    data: List[Dict]
    exported_at: datetime

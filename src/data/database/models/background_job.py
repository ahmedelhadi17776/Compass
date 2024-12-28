from typing import Text
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Enum as SQLAEnum, Index, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.sql import func
from enum import Enum


class BackgroundJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class BackgroundJob(Base):
    """Model to track background jobs."""
    __tablename__ = 'background_jobs'
    __table_args__ = (
        Index('ix_background_jobs_status', 'status'),
        Index('ix_background_jobs_created_at', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    job_type = Column(String(100), nullable=False)
    payload = Column(JSON)
    status = Column(SQLAEnum(BackgroundJobStatus),
                    nullable=False, default=BackgroundJobStatus.PENDING)
    result = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    creator = relationship("User", back_populates="background_jobs")

"""Health metrics related models."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, ForeignKey,
    Index, Float, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .user import User
from .base import Base


class EmotionalRecognition(Base):
    """Emotional recognition tracking model."""
    __tablename__ = "emotional_recognitions"
    __table_args__ = (
        Index('ix_emotional_recognitions_user_id', 'user_id'),
        Index('ix_emotional_recognitions_timestamp', 'timestamp'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete='CASCADE', name='fk_emotional_user_id'), nullable=False)
    emotion = Column(String(50), nullable=False)
    confidence_level = Column(Float, nullable=False)
    source_type = Column(String(50), nullable=False)
    source_data = Column(Text)
    recognition_metadata = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="emotional_records")


class HealthMetric(Base):
    """Health metrics tracking model."""
    __tablename__ = "health_metrics"
    __table_args__ = (
        Index('ix_health_metrics_user_id', 'user_id'),
        Index('ix_health_metrics_type', 'metric_type'),
        Index('ix_health_metrics_created', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete='CASCADE', name='fk_helath_metric_user_id'), nullable=False)
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    health_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="health_metrics")

"""AI/ML model related models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Index, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as sqlenum

from .base import Base
from Backend.utils.datetime_utils import utc_now
from enum import Enum
from .user import User


class AIModelStatus(str, Enum):
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


class AIModel(Base):
    """AI Model metadata and tracking."""
    __tablename__ = 'ai_models'
    __table_args__ = (
        Index('ix_ai_models_name_version', 'name', 'version', unique=True),
        Index('ix_ai_models_type', 'type'),
        Index('ix_ai_models_type_status', 'type', 'status'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)  # e.g., 'nlp', 'cv', 'voice'
    storage_path = Column(String(512), nullable=False)
    model_metadata = Column(JSON)
    status = Column(sqlenum(AIModelStatus), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    metrics = relationship(
        "ModelMetric", back_populates="model", cascade="all, delete-orphan")
    usage_logs = relationship(
        "ModelUsageLog", back_populates="model", cascade="all, delete-orphan")


class ModelMetric(Base):
    """Store model performance metrics."""
    __tablename__ = 'model_metrics'
    __table_args__ = (
        Index('ix_model_metrics_model_id', 'model_id'),
        Index('ix_model_metrics_timestamp', 'timestamp'),
        Index('ix_model_metrics_name', 'metric_name'),
        Index('ix_model_metrics_model_name', 'model_id', 'metric_name'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey(
        'ai_models.id', ondelete='CASCADE', name='fk_model_metrics_ai_model'), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    # e.g., 'accuracy', 'loss', 'f1'
    metric_type = Column(String(50), nullable=False)
    dataset_name = Column(String(100))  # Dataset used for metrics
    split_name = Column(String(50))  # e.g., 'train', 'validation', 'test'
    metric_data = Column(JSON)  # Changed from metadata to metric_data
    timestamp = Column(DateTime(timezone=True),
                       default=utc_now, nullable=False)

    # Relationships
    model = relationship("AIModel", back_populates="metrics")


class ModelUsageLog(Base):
    """Track AI model usage."""
    __tablename__ = "model_usage_logs"
    __table_args__ = (
        Index('ix_model_usage_logs_user_id', 'user_id'),
        Index('ix_model_usage_logs_timestamp', 'timestamp'),
        Index('ix_model_usage_logs_model', 'model_name'),
        Index('ix_model_usage_logs_user_model', 'user_id', 'model_name'),
        CheckConstraint('execution_time_ms >= 0 AND memory_usage_mb >= 0 AND cpu_usage_percent >= 0 AND cpu_usage_percent <= 100 AND gpu_usage_percent >= 0 AND gpu_usage_percent <= 100 AND cache_hit_rate >= 0 AND cache_hit_rate <= 1 AND cost >= 0', name='ck_model_usage_logs_constraints'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE',
                     name='fk_model_usage_logs_user_id'), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    # e.g., 'inference', 'training'
    operation_type = Column(String(50), nullable=False)
    input_data = Column(JSON)  # Input parameters/data
    output_data = Column(JSON)  # Model output/results
    execution_time_ms = Column(Integer)
    memory_usage_mb = Column(Float)
    cpu_usage_percent = Column(Float)
    gpu_usage_percent = Column(Float)
    status = Column(String(20), nullable=False, default='success')
    error_message = Column(String(500))
    performance_metrics = Column(JSON)  # Additional performance metrics
    timestamp = Column(DateTime(timezone=True),
                       default=utc_now, nullable=False)
    batch_id = Column(String(100))  # For grouping related operations
    tags = Column(JSON)  # For categorizing and filtering usage logs
    cost = Column(Float)  # Cost of operation if applicable
    is_cached = Column(Boolean, default=False, nullable=False)
    cache_hit_rate = Column(Float)

    # Relationships
    model = relationship("AIModel", back_populates="usage_logs")
    user = relationship("User", back_populates="model_usage_logs")

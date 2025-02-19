from sqlalchemy import Column, Integer, Float, JSON, ForeignKey, DateTime, String, Index
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime


class ProductivityMetrics(Base):
    __tablename__ = "productivity_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)

    # Focus Time Tracking
    total_focus_time = Column(Integer)  # Minutes in focus mode
    focus_sessions = Column(Integer)  # Number of focus sessions
    average_focus_duration = Column(Float)  # Average minutes per focus session
    deep_work_periods = Column(JSON)  # Timestamps of deep work periods

    # Break Patterns
    total_break_time = Column(Integer)  # Minutes on breaks
    break_intervals = Column(JSON)  # Break timing patterns
    break_adherence_score = Column(Float)  # How well breaks were followed
    optimal_break_schedule = Column(JSON)  # AI-recommended break schedule

    # Task Completion Metrics
    tasks_completed = Column(Integer)
    tasks_in_progress = Column(Integer)
    completion_rate = Column(Float)  # Tasks completed / Total tasks
    average_completion_time = Column(Float)  # Average minutes per task
    task_completion_patterns = Column(JSON)  # Time patterns of task completion

    # Workflow Efficiency
    context_switches = Column(Integer)  # Number of task switches
    workflow_optimization_score = Column(Float)  # 0-1 efficiency score
    bottleneck_analysis = Column(JSON)  # Identified workflow bottlenecks

    # Time Management
    time_allocation = Column(JSON)  # Time spent on different activities
    meeting_efficiency = Column(Float)  # Meeting productivity score
    idle_time = Column(Integer)  # Minutes of detected idle time
    overtime_patterns = Column(JSON)  # Patterns of work beyond schedule

    # AI-Generated Insights
    productivity_insights = Column(JSON)  # AI analysis of productivity
    improvement_suggestions = Column(JSON)  # AI-generated recommendations
    productivity_trends = Column(JSON)  # Historical trend analysis

    # Relationships
    user = relationship("User", back_populates="productivity_metrics")

    __table_args__ = (
        Index("ix_productivity_metrics_user_id", "user_id"),
        Index("ix_productivity_metrics_date", "date"),
    )

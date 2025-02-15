from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime

class ProductivityMetrics(Base):
    __tablename__ = "productivity_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    screen_time = Column(Integer)  # in seconds
    focus_score = Column(Float)
    focus_sessions = Column(Integer)
    interruptions = Column(Integer)
    active_apps = Column(JSON)  # Track which apps were used
    typing_speed = Column(Float)  # words per minute
    mouse_clicks = Column(Integer)
    idle_time = Column(Integer)  # in seconds
    focus_mode_enabled = Column(Boolean, default=False)
    stress_indicators = Column(JSON)  # Store stress-related metrics
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="productivity_metrics")

    __table_args__ = (
        Index("ix_productivity_metrics_user_id", "user_id"),
        Index("ix_productivity_metrics_date", "date"),
        Index("ix_productivity_metrics_focus_score", "focus_score"),
    ) 
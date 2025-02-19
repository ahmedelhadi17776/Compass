from sqlalchemy import Column, Integer, Float, JSON, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime

class EmotionalMetrics(Base):
    __tablename__ = "emotional_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    stress_level = Column(Float)  # 0-1 scale
    fatigue_indicators = Column(JSON)  # Eye strain, posture issues, etc.
    voice_analysis = Column(JSON)  # Voice pattern analysis results
    facial_expressions = Column(JSON)  # Detected emotions from facial analysis
    break_recommendations = Column(JSON)  # AI-generated break suggestions
    wellness_score = Column(Float)  # Overall wellness indicator
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="emotional_metrics")

    __table_args__ = (
        Index("ix_emotional_metrics_user_id", "user_id"),
        Index("ix_emotional_metrics_timestamp", "timestamp"),
        Index("ix_emotional_metrics_stress_level", "stress_level"),
        Index("ix_emotional_metrics_wellness_score", "wellness_score"),
    ) 
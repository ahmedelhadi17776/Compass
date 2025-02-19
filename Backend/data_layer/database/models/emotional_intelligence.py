from sqlalchemy import Column, Integer, Float, JSON, ForeignKey, DateTime, String, Index
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime


class EmotionalIntelligence(Base):
    __tablename__ = "emotional_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Stress Indicators
    stress_level = Column(Float)  # 0-1 scale
    stress_factors = Column(JSON)  # Contributing factors to stress

    # Fatigue Detection
    fatigue_score = Column(Float)  # 0-1 scale
    screen_time = Column(Integer)  # Minutes
    break_frequency = Column(Integer)  # Minutes between breaks
    posture_score = Column(Float)  # 0-1 scale

    # Work Pattern Analysis
    focus_duration = Column(Integer)  # Minutes of focused work
    distraction_count = Column(Integer)
    productivity_score = Column(Float)  # 0-1 scale
    work_rhythm_pattern = Column(JSON)  # Daily work pattern data

    # Environmental Factors
    noise_level = Column(Float)  # Ambient noise level
    lighting_condition = Column(String(50))
    workspace_ergonomics = Column(JSON)  # Ergonomic factors

    # Cognitive Load
    cognitive_load_score = Column(Float)  # 0-1 scale
    task_complexity_level = Column(Integer)  # 1-5 scale
    context_switching_frequency = Column(
        Integer)  # Number of switches per hour

    # Relationships
    user = relationship("User", back_populates="emotional_data")

    __table_args__ = (
        Index("ix_emotional_intelligence_user_id", "user_id"),
        Index("ix_emotional_intelligence_timestamp", "timestamp"),
    )

from sqlalchemy import Column, Integer, JSON, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime

class UserWorkspaceSettings(Base):
    __tablename__ = "user_workspace_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    clipboard_history = Column(JSON)  # Recent clipboard items
    focus_mode_settings = Column(JSON)  # Focus mode preferences
    distraction_blocker_rules = Column(JSON)  # Rules for blocking distractions
    screen_time_limits = Column(JSON)  # Daily screen time limits
    break_reminder_settings = Column(JSON)  # Break reminder preferences
    eye_care_settings = Column(JSON)  # Screen brightness and blue light settings
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="workspace_settings")

    __table_args__ = (
        Index("ix_workspace_settings_user_id", "user_id"),
    ) 
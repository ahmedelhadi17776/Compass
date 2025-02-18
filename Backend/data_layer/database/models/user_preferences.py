from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    theme = Column(String(50))
    language = Column(String(50))
    timezone = Column(String(50))
    date_format = Column(String(50))
    time_format = Column(String(50))
    notifications_enabled = Column(Boolean, default=True)
    accessibility_settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences")

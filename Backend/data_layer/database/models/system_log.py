from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(50))
    category = Column(String(100))
    message = Column(Text)
    details = Column(JSON)
    source = Column(String(100))
    trace_id = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("ix_system_logs_level", "level"),
        Index("ix_system_logs_category", "category"),
        Index("ix_system_logs_user_id", "user_id"),
        Index("ix_system_logs_created_at", "created_at"),
    )

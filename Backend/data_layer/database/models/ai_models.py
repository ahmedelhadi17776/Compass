from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    request_id = Column(String(100))
    action_data = Column(JSON)
    result = Column(JSON)
    status = Column(String(50))
    error_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("ix_agent_action_agent_type", "agent_type"),
        Index("ix_agent_action_user_id", "user_id"),
        Index("ix_agent_action_status", "status"),
        Index("ix_agent_action_timestamp", "timestamp"),
    )

    # Relationships
    user = relationship("User")
    feedback = relationship(
        "AgentFeedback", back_populates="action", cascade="all, delete-orphan")


class AgentFeedback(Base):
    __tablename__ = "agent_feedback"

    id = Column(Integer, primary_key=True, index=True)
    agent_action_id = Column(Integer, ForeignKey(
        "agent_actions.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"))
    feedback_score = Column(Integer)
    feedback_text = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    action = relationship("AgentAction", back_populates="feedback")
    user = relationship("User")


class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50))
    type = Column(String(100))
    storage_path = Column(String(255))
    model_metadata = Column(JSON)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        Index("ix_ai_model_name_version", "name", "version", unique=True),
        Index("ix_ai_model_type", "type"),
        Index("ix_ai_model_status", "status"),
    )


class AgentType(Base):
    __tablename__ = "agent_types"

    type = Column(String(100), primary_key=True)
    description = Column(Text)


class ModelType(Base):
    __tablename__ = "model_types"

    type = Column(String(100), primary_key=True)
    description = Column(Text)

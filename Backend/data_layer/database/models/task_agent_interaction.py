from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Float, Index
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime

class TaskAgentInteraction(Base):
    __tablename__ = "task_agent_interactions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))
    agent_id = Column(Integer, ForeignKey("agent_actions.id"))
    interaction_type = Column(String(100))
    confidence_score = Column(Float)
    recommendations = Column(JSON)
    action_taken = Column(String(100))
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="agent_interactions")
    agent = relationship("AgentAction")

    __table_args__ = (
        Index("ix_task_agent_interactions_task_id", "task_id"),
        Index("ix_task_agent_interactions_agent_id", "agent_id"),
        Index("ix_task_agent_interactions_created_at", "created_at"),
    )
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Float, Index, Boolean
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime

class WorkflowAgentInteraction(Base):
    __tablename__ = "workflow_agent_interactions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"))
    agent_id = Column(Integer, ForeignKey("agent_actions.id"))
    interaction_type = Column(String(100))
    confidence_score = Column(Float)
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_time = Column(Float)
    status = Column(String(50))
    error_message = Column(Text)
    performance_metrics = Column(JSON)
    optimization_suggestions = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="agent_interactions")
    agent = relationship("AgentAction")

    __table_args__ = (
        Index("ix_workflow_agent_interactions_workflow_id", "workflow_id"),
        Index("ix_workflow_agent_interactions_agent_id", "agent_id"),
        Index("ix_workflow_agent_interactions_created_at", "created_at"),
        Index("ix_workflow_agent_interactions_status", "status"),
    )
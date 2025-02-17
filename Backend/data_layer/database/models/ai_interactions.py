from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Float, Index, Boolean
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime

class RAGQuery(Base):
    __tablename__ = "rag_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query_text = Column(Text, nullable=False)
    context_used = Column(JSON)  # Retrieved context chunks
    response = Column(Text)
    relevance_score = Column(Float)  # How relevant was the response
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="rag_queries")

    __table_args__ = (
        Index("ix_rag_queries_user_id", "user_id"),
        Index("ix_rag_queries_created_at", "created_at"),
    )

class EmailOrganization(Base):
    __tablename__ = "email_organization"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email_rules = Column(JSON)  # Custom organization rules
    priority_settings = Column(JSON)  # Email priority preferences
    auto_reply_templates = Column(JSON)  # Templates for AI-generated replies
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="email_organization")

    __table_args__ = (
        Index("ix_email_organization_user_id", "user_id"),
    )

class AIAgentInteraction(Base):
    __tablename__ = "ai_agent_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ai_model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=False)
    agent_type = Column(String(100))  # e.g., "email", "research", "task"
    interaction_type = Column(String(100))  # e.g., "query", "suggestion", "action"
    input_data = Column(JSON)
    output_data = Column(JSON)
    success_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Model versioning and metadata
    model_version = Column(String(50), nullable=False)  # Specific version of the AI model
    model_parameters = Column(JSON)  # Parameters used for this interaction
    execution_time = Column(Float)  # Time taken to process in seconds
    token_usage = Column(JSON)  # Token consumption metrics
    cache_hit = Column(Boolean, default=False)  # Whether result was cached
    error_logs = Column(JSON)  # Any errors or warnings during processing
    performance_metrics = Column(JSON)  # Detailed performance data
    feedback_score = Column(Float)  # User feedback if provided
    was_helpful = Column(Boolean)  # User found the interaction helpful
    improvement_suggestions = Column(Text)  # User suggestions for improvement

    # Relationships
    user = relationship("User", back_populates="ai_interactions")
    ai_model = relationship("AIModel", back_populates="interactions")

    __table_args__ = (
        Index("ix_ai_agent_interactions_user_id", "user_id"),
        Index("ix_ai_agent_interactions_agent_type", "agent_type"),
        Index("ix_ai_agent_interactions_created_at", "created_at"),
        Index("ix_ai_agent_interactions_model_version", "model_version"),
        Index("ix_ai_agent_interactions_success_rate", "success_rate"),
        Index("ix_ai_agent_interactions_feedback_score", "feedback_score"),
    ) 
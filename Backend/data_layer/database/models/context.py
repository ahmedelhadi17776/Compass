from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, LargeBinary, Index
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime


class ContextSnapshot(Base):
    __tablename__ = "context_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    multimodal_data = Column(JSON)
    derived_context = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    embeddings = Column(LargeBinary)
    source_url = Column(String(255))
    entity_name = Column(String(255))
    relationships = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id"))
    last_accessed = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("ix_knowledge_base_entity_name", "entity_name"),
        Index("ix_knowledge_base_user_id", "user_id"),
    )

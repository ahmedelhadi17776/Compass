"""Summary models module."""
from datetime import timedelta
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, 
    Index, JSON, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.data.database.models.user import User
from src.data.database.base import Base
from src.data.cache import CacheEntry  
from src.utils import datetime_utils


class Summary(Base):
    """Model for storing AI-generated summaries."""
    __tablename__ = "summaries"
    __table_args__ = (
        Index('ix_summaries_content_type_id', 'content_type', 'content_id', unique=True),
        Index('ix_summaries_created_at', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    content_type = Column(String(50), nullable=False)  # 'task', 'conversation', 'document'
    content_id = Column(Integer, nullable=False)
    summary = Column(Text, nullable=False)
    key_points = Column(JSON)
    language = Column(String(10), nullable=False, default='en')
    model_version = Column(String(50))
    confidence_score = Column(Float)
    extra_info = Column(JSON)
    word_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_validated_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Summary(id={self.id}, type={self.content_type}, content_id={self.content_id})>"
    
    def cache_summary(self, session):
        """Cache the generated summary."""
        cache_entry = CacheEntry(
            cache_key=f"summary_{self.content_id}",
            cache_value=self.summary,
            expires_at=datetime_utils.utcnow() + timedelta(hours=1),  # Set expiration time
            user_id=self.user_id  # Link to the user
        )
        session.add(cache_entry)
        session.commit()

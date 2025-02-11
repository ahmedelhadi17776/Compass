"""Web search and cache related models."""
from datetime import timedelta
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, ForeignKey,
    Index, Text, Boolean, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .user import User
from .cache import CacheEntry
from .base import Base

from ....utils import datetime_utils


class WebSearchQuery(Base):
    """Store web search queries and results."""
    __tablename__ = 'web_search_queries'
    __table_args__ = (
        Index('ix_web_search_queries_user_id', 'user_id'),
        Index('ix_web_search_queries_timestamp', 'execution_time'),
        Index('ix_web_search_queries_type', 'search_type'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    search_type = Column(String(50), nullable=False)  # web, image, news
    filters = Column(JSON)
    results = Column(JSON)
    result_count = Column(Integer)
    execution_time = Column(Float)
    is_cached = Column(Boolean, default=False)
    cache_hit = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="web_searches")

    def cache_results(self, session):
        """Cache the results of the web search query."""
        cache_entry = CacheEntry(
            cache_key=self.query_text,
            cache_value=self.results,
            expires_at=datetime_utils.utcnow() + timedelta(hours=1),  # Set expiration time
            user_id=self.user_id  # Link to the user
        )
        session.add(cache_entry)
        session.commit()

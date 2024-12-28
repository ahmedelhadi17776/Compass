"""Cache entry model for storing cached data."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .user import User


class CacheEntry(Base):
    """Model for storing cache entries."""
    __tablename__ = "cache_entries"
    __table_args__ = (
        Index('ix_cache_entries_key', 'cache_key', unique=True),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    # Unique key for the cache entry
    cache_key = Column(String(255), nullable=False)
    cache_value = Column(JSON, nullable=False)  # The cached data
    # Timestamp when the entry was created
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Optional expiration timestamp
    expires_at = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", name='fk_cache_user_id'), nullable=False)  # Optional link to a user
    # Add this relationship
    user = relationship("User", back_populates="cache_entries")
    # Reverse relationship
    summary = relationship("Summary", back_populates="cache_entry")

    def __repr__(self):
        return f"<CacheEntry(id={self.id}, key='{self.cache_key}', created_at={self.created_at})>"

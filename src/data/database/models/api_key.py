from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.sql import func


class APIKey(Base):
    """Model to manage API keys for users."""
    __tablename__ = 'api_keys'
    __table_args__ = (
        Index('ix_api_keys_user', 'user_id'),
        Index('ix_api_keys_key', 'key', unique=True),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key = Column(String(255), unique=True, nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="api_keys")

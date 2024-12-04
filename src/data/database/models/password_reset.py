"""Password reset model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from ..base import Base

class PasswordReset(Base):
    """Password reset tokens table."""
    __tablename__ = "password_resets"
    __table_args__ = (
        Index('idx_password_resets_user_id', 'user_id'),
        Index('idx_password_resets_token', 'token'),
        Index('idx_password_resets_expires_at', 'expires_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="password_resets")

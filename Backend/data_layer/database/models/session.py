from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Index, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime
import enum

class SessionStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPICIOUS = "suspicious"

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True)  # For token refresh
    status = Column(SQLAlchemyEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False)
    device_info = Column(JSON)  # Device fingerprint
    ip_address = Column(String(100))
    user_agent = Column(String(255))
    location_info = Column(JSON)  # Geolocation data
    mfa_verified = Column(Boolean, default=False)  # Whether MFA was completed
    last_token_refresh = Column(DateTime)  # Last time the token was refreshed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    revoked_at = Column(DateTime)  # When the session was manually revoked
    revocation_reason = Column(String(255))  # Why the session was revoked

    # Relationship
    user = relationship("User", back_populates="sessions")
    security_logs = relationship("SecurityAuditLog", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_status", "status"),
        Index("ix_sessions_expires_at", "expires_at"),
        Index("ix_sessions_last_activity", "last_activity"),
    )

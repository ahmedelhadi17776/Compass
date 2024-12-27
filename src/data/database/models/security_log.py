"""Security audit log models."""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from src.data.database.base import Base


class SecurityAuditLog(Base):
    """Security audit log model."""

    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String)
    user_agent = Column(String)
    request_path = Column(String)
    request_method = Column(String)
    details = Column(JSON)


class SecurityEvent(Base):
    """Security event model."""

    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String)
    severity = Column(String)
    description = Column(String)
    metadata = Column(JSON)

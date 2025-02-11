"""Security audit log models."""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from .import Base
from sqlalchemy.orm import relationship


class SecurityAuditLog(Base):
    """Security audit log model."""

    __tablename__ = "security_audit_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String)
    user_agent = Column(String)
    request_path = Column(String)
    request_method = Column(String)
    details = Column(JSON)

    # Relationships
    user = relationship("User", back_populates="security_audit_logs")

    def __repr__(self):
        return f"<SecurityAuditLog(id={self.id}, user_id={self.user_id}, action='{self.event_type}')>"


class SecurityEvent(Base):
    """Model for tracking security events."""
    __tablename__ = "security_events"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String)
    severity = Column(String)
    description = Column(String)
    event_metadata = Column(String(500))

    user = relationship("User", back_populates="security_events")


    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, user_id={self.user_id}, action='{self.action}')>"

from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime


class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_type = Column(String(100))
    ip_address = Column(String(100))
    user_agent = Column(String(255))
    request_path = Column(String(255))
    request_method = Column(String(20))
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("ix_security_audit_logs_user_id", "user_id"),
        Index("ix_security_audit_logs_event_type", "event_type"),
    )

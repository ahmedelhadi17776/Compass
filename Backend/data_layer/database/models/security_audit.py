from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Index, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime
import enum

class AuditEventType(enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    MFA_CHANGE = "mfa_change"
    PERMISSION_CHANGE = "permission_change"
    ROLE_CHANGE = "role_change"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SECURITY_SETTING_CHANGE = "security_setting_change"
    SESSION_EXPIRED = "session_expired"
    FAILED_LOGIN = "failed_login"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="SET NULL"))
    event_type = Column(SQLAlchemyEnum(AuditEventType), nullable=False)
    ip_address = Column(String(100))
    user_agent = Column(String(255))
    request_path = Column(String(255))
    request_method = Column(String(20))
    status_code = Column(Integer)  # HTTP status code
    failure_reason = Column(String(255))  # For failed attempts
    risk_score = Column(Integer)  # 0-100 risk assessment
    details = Column(JSON)  # Additional event details
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="security_logs")
    session = relationship("Session", back_populates="security_logs")

    __table_args__ = (
        Index("ix_security_audit_logs_user_id", "user_id"),
        Index("ix_security_audit_logs_event_type", "event_type"),
        Index("ix_security_audit_logs_created_at", "created_at"),
        Index("ix_security_audit_logs_ip_address", "ip_address"),
        Index("ix_security_audit_logs_risk_score", "risk_score"),
    )

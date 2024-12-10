"""Integration and API management models."""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Boolean, JSON, Index, Text, Enum as SQLAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .user import User
from .base import Base

class IntegrationType(str, Enum):
    """Integration type enum."""
    API = "api"
    OAUTH = "oauth"
    WEBHOOK = "webhook"
    DATABASE = "database"
    CUSTOM = "custom"

class IntegrationStatus(str, Enum):
    """Integration status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class Integration(Base):
    """External integration model."""
    __tablename__ = "integrations"
    __table_args__ = (
        Index('ix_integrations_type', 'integration_type'),
        Index('ix_integrations_status', 'status'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    integration_type = Column(SQLAEnum(IntegrationType), nullable=False)
    status = Column(SQLAEnum(IntegrationStatus), nullable=False, default=IntegrationStatus.PENDING)
    
    # Configuration
    config = Column(JSON, nullable=False)  # Connection details, endpoints, etc.
    credentials = Column(JSON)  # Encrypted credentials
    headers = Column(JSON)  # Custom headers
    
    # Settings
    retry_config = Column(JSON)  # Retry settings
    rate_limit = Column(JSON)  # Rate limiting settings
    timeout = Column(Integer)  # Timeout in seconds
    
    # Monitoring
    health_check_url = Column(String(500))
    last_health_check = Column(DateTime(timezone=True))
    error_count = Column(Integer, default=0)
    last_error = Column(String(500))
    
    # Metadata
    description = Column(String(500))
    version = Column(String(50))
    documentation_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    logs = relationship("IntegrationLog", back_populates="integration", cascade="all, delete-orphan")

class IntegrationLog(Base):
    """Integration activity logging model."""
    __tablename__ = "integration_logs"
    __table_args__ = (
        Index('ix_integration_logs_integration', 'integration_id'),
        Index('ix_integration_logs_status', 'status'),
        Index('ix_integration_logs_created', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    integration_id = Column(Integer, ForeignKey("integrations.id", ondelete='CASCADE',name='fk_log_integration'), nullable=False)
    
    # Request Details
    endpoint = Column(String(500))
    method = Column(String(10))
    request_data = Column(JSON)
    response_data = Column(JSON)
    status_code = Column(Integer)
    status = Column(String(50), nullable=False)
    
    # Performance
    duration = Column(Integer)  # Response time in milliseconds
    size = Column(Integer)  # Response size in bytes
    
    # Error Handling
    error_message = Column(String(500))
    stack_trace = Column(Text)
    
    # Metadata
    correlation_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    integration = relationship("Integration", back_populates="logs") 
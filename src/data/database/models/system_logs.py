"""System logging and file management models."""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, JSON, Index, Enum as SQLAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .user import User
from .base import Base

class LogLevel(str, Enum):
    """Log level enum."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory(str, Enum):
    """Log category enum."""
    SYSTEM = "system"
    APPLICATION = "application"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATABASE = "database"
    INTEGRATION = "integration"
    USER = "user"

class SystemLog(Base):
    """System log model."""
    __tablename__ = "system_logs"
    __table_args__ = (
        Index('ix_system_logs_level', 'level'),
        Index('ix_system_logs_category', 'category'),
        Index('ix_system_logs_created', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    level = Column(SQLAEnum(LogLevel), nullable=False, default=LogLevel.INFO)
    category = Column(SQLAEnum(LogCategory), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON)
    
    # Context
    source = Column(String(255))  # Component/module generating the log
    trace_id = Column(String(100))  # For request tracing
    user_id = Column(Integer, ForeignKey("User.id", ondelete='SET NULL',name='fk_sys_log_user_id'))
    
    # Technical Details
    stack_trace = Column(Text)
    request_data = Column(JSON)
    environment = Column(JSON)  # Environment details
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    host = Column(String(255))

    # Relationships
    user = relationship("User", back_populates="system_logs")

class FileLog(Base):
    """File operation logging model."""
    __tablename__ = "file_logs"
    __table_args__ = (
        Index('ix_file_logs_user', 'user_id'),
        Index('ix_file_logs_operation', 'operation'),
        Index('ix_file_logs_created', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete='SET NULL',name='fk_file_log_user_id'))
    file_path = Column(String(1000), nullable=False)
    operation = Column(String(50), nullable=False)  # CREATE, READ, UPDATE, DELETE
    status = Column(String(50), nullable=False)
    size = Column(Integer)  # File size in bytes
    checksum = Column(String(64))  # File hash
    extra_informations = Column(JSON)
    error_message = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="file_logs")

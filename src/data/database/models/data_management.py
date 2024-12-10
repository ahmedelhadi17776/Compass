"""Data archive and request management models."""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    JSON, Index, Enum as SQLAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .user import User

from .base import Base

class DataRequestType(str, Enum):
    """Data request type enum."""
    EXPORT = "export"
    DELETION = "deletion"
    ACCESS = "access"
    CORRECTION = "correction"

class DataRequestStatus(str, Enum):
    """Data request status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DataRequest(Base):
    """Data request model."""
    __tablename__ = "data_requests"
    __table_args__ = (
        Index('ix_data_requests_user', 'user_id'),
        Index('ix_data_requests_type', 'request_type'),
        Index('ix_data_requests_status', 'status'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete='CASCADE', name='fk_data_request_user_id'), nullable=False)
    request_type = Column(SQLAEnum(DataRequestType), nullable=False)
    status = Column(SQLAEnum(DataRequestStatus), nullable=False, default=DataRequestStatus.PENDING)
    
    # Request Details
    data_types = Column(JSON, nullable=False)  # Types of data requested
    date_range = Column(JSON)  # Optional date range for data
    format = Column(String(50))  # Requested format (e.g., 'json', 'csv')
    reason = Column(String(500))
    
    # Processing
    download_url = Column(String(1000))
    file_size = Column(Integer)  # Size in bytes
    expiry_date = Column(DateTime(timezone=True))
    error_message = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="data_requests")
    archives = relationship("DataArchive", back_populates="data_request")

class DataArchive(Base):
    """Data archive model."""
    __tablename__ = "data_archives"
    __table_args__ = (
        Index('ix_data_archives_request', 'request_id'),
        Index('ix_data_archives_type', 'data_type'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("data_requests.id", ondelete='CASCADE', name='fk_data_archive_data_requests'))
    data_type = Column(String(100), nullable=False)
    original_id = Column(Integer)
    content = Column(JSON, nullable=False)
    more_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    data_request = relationship("DataRequest", back_populates="archives") 
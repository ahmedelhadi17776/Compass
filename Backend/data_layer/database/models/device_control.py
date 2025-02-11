"""Device control and monitoring models."""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    JSON, Float, Boolean, Index, Enum as SQLAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .user import User
from .base import Base


class DeviceType(str, Enum):
    """Device types enum."""
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    CAMERA = "camera"
    DISPLAY = "display"
    AUDIO = "audio"
    CUSTOM = "custom"


class DeviceStatus(str, Enum):
    """Device status enum."""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    DISABLED = "disabled"


class DeviceControl(Base):
    """Device control and monitoring model."""
    __tablename__ = "device_controls"
    __table_args__ = (
        Index('ix_device_controls_user', 'user_id'),
        Index('ix_device_controls_type', 'device_type'),
        Index('ix_device_controls_status', 'status'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete='CASCADE', name='fk_device_control_user_id'), nullable=False)
    device_id = Column(String(100), nullable=False)
    device_name = Column(String(255), nullable=False)
    device_type = Column(SQLAEnum(DeviceType), nullable=False)
    status = Column(SQLAEnum(DeviceStatus), nullable=False,
                    default=DeviceStatus.OFFLINE)

    # Device Details
    manufacturer = Column(String(100))
    model = Column(String(100))
    firmware_version = Column(String(50))
    capabilities = Column(JSON)  # Available functions/features
    configuration = Column(JSON)  # Current settings

    # Monitoring
    last_ping = Column(DateTime(timezone=True))
    battery_level = Column(Float)
    signal_strength = Column(Float)
    temperature = Column(Float)

    # Control
    is_active = Column(Boolean, default=True, nullable=False)
    auto_connect = Column(Boolean, default=True, nullable=False)
    maintenance_mode = Column(Boolean, default=False, nullable=False)

    # Metadata
    location = Column(JSON)  # Physical location data
    tags = Column(JSON)  # Custom tags/labels
    notes = Column(String(500))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="device_controls")
    control_logs = relationship(
        "DeviceControlLog", back_populates="device", cascade="all, delete-orphan")


class DeviceControlLog(Base):
    """Device control action logging."""
    __tablename__ = "device_control_logs"
    __table_args__ = (
        Index('idx_device_control_logs_device', 'device_id'),
        Index('idx_device_control_logs_user', 'user_id'),
        Index('idx_device_control_logs_created', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("device_controls.id",
                       ondelete='CASCADE', name='fk_device_log_device_id'), nullable=False)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete='CASCADE', name='fk_device_log_user_id'), nullable=False)
    action = Column(String(100), nullable=False)
    parameters = Column(JSON)
    result = Column(JSON)
    status = Column(String(50), nullable=False)
    error_message = Column(String(500))
    execution_time = Column(Float)  # in milliseconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    device = relationship("DeviceControl", back_populates="control_logs")
    user = relationship("User", back_populates="device_logs")

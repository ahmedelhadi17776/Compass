"""Privacy settings schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class PrivacySettingsBase(BaseModel):
    """Base privacy settings schema."""

    data_collection: bool = Field(True, description="Allow data collection")
    data_sharing: bool = Field(False, description="Allow data sharing")
    marketing_communications: bool = Field(False, description="Allow marketing communications")
    analytics_tracking: bool = Field(True, description="Allow analytics tracking")

class PrivacySettingsCreate(PrivacySettingsBase):
    """Create privacy settings schema."""

    pass

class PrivacySettingsUpdate(BaseModel):
    """Update privacy settings schema."""

    data_collection: Optional[bool] = None
    data_sharing: Optional[bool] = None
    marketing_communications: Optional[bool] = None
    analytics_tracking: Optional[bool] = None

class PrivacySettings(PrivacySettingsBase):
    """Privacy settings schema."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        orm_mode = True

class DataRequestBase(BaseModel):
    """Base data request schema."""

    type: str = Field(..., description="Type of request (export/deletion)")
    data_types: List[str] = Field(..., description="Types of data to process")
    reason: Optional[str] = Field(None, description="Reason for request")

class DataRequestCreate(DataRequestBase):
    """Create data request schema."""

    pass

class DataRequestUpdate(BaseModel):
    """Update data request schema."""

    status: Optional[str] = None
    download_url: Optional[str] = None

class DataRequest(DataRequestBase):
    """Data request schema."""

    id: int
    user_id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None

    class Config:
        """Pydantic config."""

        orm_mode = True

class DataRequestStatus(BaseModel):
    """Data request status schema."""

    request_id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None

class PrivacyReport(BaseModel):
    """Privacy report schema."""

    period: dict
    data_requests: dict
    privacy_settings: dict
    data_retention: dict
    generated_at: datetime

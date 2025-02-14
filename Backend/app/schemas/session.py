from pydantic import BaseModel
from datetime import datetime
from data_layer.database.models.session import SessionStatus


class SessionResponse(BaseModel):
    id: int
    user_id: int
    token: str
    status: SessionStatus
    device_info: dict | None
    ip_address: str | None
    user_agent: str | None
    location_info: dict | None
    mfa_verified: bool
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    is_valid: bool

    class Config:
        from_attributes = True

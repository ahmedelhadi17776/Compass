from pydantic import BaseModel
from datetime import datetime


class SessionResponse(BaseModel):
    id: int
    user_id: int
    device_info: str | None
    ip_address: str | None
    is_valid: bool
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

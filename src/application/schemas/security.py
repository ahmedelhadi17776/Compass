from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime


class SecurityAlert(BaseModel):
    event_type: str
    details: Dict[str, Any]
    severity: str
    timestamp: datetime


class ActiveThreat(BaseModel):
    type: str
    severity: str
    description: str
    timestamp: datetime
    details: Dict[str, Any]


class ActiveThreats(BaseModel):
    active_threats: int
    threats: List[ActiveThreat]

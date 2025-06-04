from pydantic import BaseModel
from typing import Optional, Dict, Any


class DashboardMetrics(BaseModel):
    habits: Optional[Dict[str, Any]] = None
    calendar: Optional[Dict[str, Any]] = None
    focus: Optional[Dict[str, Any]] = None
    mood: Optional[Dict[str, Any]] = None
    ai_usage: Optional[Dict[str, Any]] = None
    shared_events: Optional[Dict[str, Any]] = None
    system_metrics: Optional[Dict[str, Any]] = None
    goals: Optional[Dict[str, Any]] = None
    tasks: Optional[Dict[str, Any]] = None
    todos: Optional[Dict[str, Any]] = None
    projects: Optional[Dict[str, Any]] = None
    workflows: Optional[Dict[str, Any]] = None
    user: Optional[Dict[str, Any]] = None
    notes: Optional[Dict[str, Any]] = None
    journals: Optional[Dict[str, Any]] = None
    cost: Optional[Dict[str, Any]] = None

"""Utility functions for datetime handling."""
from datetime import datetime, timezone

def utc_now() -> datetime:
    """Get current UTC datetime with timezone information."""
    return datetime.now(timezone.utc)

def make_aware(dt: datetime) -> datetime:
    """Convert naive datetime to timezone-aware UTC datetime."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

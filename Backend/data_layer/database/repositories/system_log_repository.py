"""Repository for System Log related database operations."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.system_logs import SystemLog, File
from .base_repository import BaseRepository

class SystemLogRepository(BaseRepository[SystemLog]):
    """Repository for System Log operations."""

    def __init__(self, session: Session):
        super().__init__(SystemLog, session)

    def get_by_severity(self, severity: str) -> List[SystemLog]:
        """Get logs by severity level."""
        return self.session.query(SystemLog).filter(
            SystemLog.severity == severity
        ).all()

    def get_by_source(self, source: str) -> List[SystemLog]:
        """Get logs by source."""
        return self.session.query(SystemLog).filter(
            SystemLog.source == source
        ).all()

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[SystemLog]:
        """Get logs within a date range."""
        return self.session.query(SystemLog).filter(
            and_(
                SystemLog.created_at >= start_date,
                SystemLog.created_at <= end_date
            )
        ).all()

class FileRepository(BaseRepository[File]):
    """Repository for File operations."""

    def __init__(self, session: Session):
        super().__init__(File, session)

    def get_by_type(self, file_type: str) -> List[File]:
        """Get files by type."""
        return self.session.query(File).filter(
            File.file_type == file_type
        ).all()

    def get_by_hash(self, file_hash: str) -> Optional[File]:
        """Get file by hash."""
        return self.session.query(File).filter(
            File.hash == file_hash
        ).first()

    def get_by_tags(self, tags: List[str]) -> List[File]:
        """Get files by tags."""
        return self.session.query(File).filter(
            File.tags.contains(tags)
        ).all()

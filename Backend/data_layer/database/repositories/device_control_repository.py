"""Repository for Device Control related database operations."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.device_control import DeviceControlLog, EmotionalRecognition
from .base_repository import BaseRepository

class DeviceControlRepository(BaseRepository[DeviceControlLog]):
    """Repository for Device Control operations."""

    def __init__(self, session: Session):
        super().__init__(DeviceControlLog, session)

    def get_device_logs(self, device_id: str) -> List[DeviceControlLog]:
        """Get logs for a specific device."""
        return self.session.query(DeviceControlLog).filter(
            DeviceControlLog.device_id == device_id
        ).all()

    def get_by_status(self, status: str) -> List[DeviceControlLog]:
        """Get logs by status."""
        return self.session.query(DeviceControlLog).filter(
            DeviceControlLog.status == status
        ).all()

class EmotionalRecognitionRepository(BaseRepository[EmotionalRecognition]):
    """Repository for Emotional Recognition operations."""

    def __init__(self, session: Session):
        super().__init__(EmotionalRecognition, session)

    def get_by_source(self, source: str) -> List[EmotionalRecognition]:
        """Get emotional recognition records by source."""
        return self.session.query(EmotionalRecognition).filter(
            EmotionalRecognition.source == source
        ).all()

    def get_by_emotion(self, emotion: str) -> List[EmotionalRecognition]:
        """Get records by emotion type."""
        return self.session.query(EmotionalRecognition).filter(
            EmotionalRecognition.emotion == emotion
        ).all()

    def get_high_confidence(self, threshold: float = 0.8) -> List[EmotionalRecognition]:
        """Get high confidence emotional recognition records."""
        return self.session.query(EmotionalRecognition).filter(
            EmotionalRecognition.confidence >= threshold
        ).all()

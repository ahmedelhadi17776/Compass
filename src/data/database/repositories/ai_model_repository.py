"""Repository for AI Model related database operations."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.ai_model import AIModel, ModelUsageLog, ModelMetrics
from .base_repository import BaseRepository

class AIModelRepository(BaseRepository[AIModel]):
    """Repository for AI Model operations."""

    def __init__(self, session: Session):
        super().__init__(AIModel, session)

    def get_by_name_version(self, name: str, version: str) -> Optional[AIModel]:
        """Get model by name and version."""
        return self.session.query(AIModel).filter(
            and_(AIModel.name == name, AIModel.version == version)
        ).first()

    def get_active_models(self) -> List[AIModel]:
        """Get all active models."""
        return self.session.query(AIModel).filter(AIModel.status == 'active').all()

    def get_production_models(self) -> List[AIModel]:
        """Get all production models."""
        return self.session.query(AIModel).filter(AIModel.is_production == True).all()

class ModelUsageLogRepository(BaseRepository[ModelUsageLog]):
    """Repository for Model Usage Log operations."""

    def __init__(self, session: Session):
        super().__init__(ModelUsageLog, session)

    def get_model_usage(self, model_id: int) -> List[ModelUsageLog]:
        """Get usage logs for a specific model."""
        return self.session.query(ModelUsageLog).filter(
            ModelUsageLog.model_id == model_id
        ).all()

    def get_user_usage(self, user_id: int) -> List[ModelUsageLog]:
        """Get usage logs for a specific user."""
        return self.session.query(ModelUsageLog).filter(
            ModelUsageLog.user_id == user_id
        ).all()

class ModelMetricsRepository(BaseRepository[ModelMetrics]):
    """Repository for Model Metrics operations."""

    def __init__(self, session: Session):
        super().__init__(ModelMetrics, session)

    def get_model_metrics(self, model_id: int) -> List[ModelMetrics]:
        """Get metrics for a specific model."""
        return self.session.query(ModelMetrics).filter(
            ModelMetrics.model_id == model_id
        ).all()

    def get_latest_metrics(self, model_id: int, metric_name: str) -> Optional[ModelMetrics]:
        """Get latest metrics for a specific model and metric name."""
        return self.session.query(ModelMetrics).filter(
            and_(
                ModelMetrics.model_id == model_id,
                ModelMetrics.metric_name == metric_name
            )
        ).order_by(ModelMetrics.timestamp.desc()).first()

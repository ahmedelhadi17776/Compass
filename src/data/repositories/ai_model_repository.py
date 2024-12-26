"""AI Model repository module."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.ai_model import AIModel
from ..database.models.ai_usage import AIUsage
from core.exceptions import ModelNotFoundError

class AIModelRepository:
    """AI Model repository class."""

    def __init__(self, session: AsyncSession):
        """Initialize AI model repository."""
        self._session = session

    async def create_model(self, model_data: dict) -> AIModel:
        """Create a new AI model entry."""
        model = AIModel(
            name=model_data["name"],
            version=model_data["version"],
            type=model_data["type"],
            description=model_data.get("description"),
            parameters=model_data.get("parameters"),
            status=model_data.get("status", "active")
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def get_model(self, model_id: int) -> AIModel:
        """Get an AI model by ID."""
        model = await self._session.execute(
            select(AIModel).where(AIModel.id == model_id)
        )
        model = model.scalar_one_or_none()
        if not model:
            raise ModelNotFoundError(f"AI Model with id {model_id} not found")
        return model

    async def get_models_by_type(self, model_type: str) -> List[AIModel]:
        """Get all models of a specific type."""
        models = await self._session.execute(
            select(AIModel).where(AIModel.type == model_type)
        )
        return models.scalars().all()

    async def update_model(self, model_id: int, model_data: dict) -> AIModel:
        """Update an AI model."""
        model = await self.get_model(model_id)
        for key, value in model_data.items():
            if hasattr(model, key) and value is not None:
                setattr(model, key, value)
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def log_model_usage(self, usage_data: dict) -> AIUsage:
        """Log AI model usage."""
        usage = AIUsage(
            model_id=usage_data["model_id"],
            user_id=usage_data["user_id"],
            request_type=usage_data["request_type"],
            input_data=usage_data.get("input_data"),
            output_data=usage_data.get("output_data"),
            execution_time=usage_data.get("execution_time"),
            status=usage_data.get("status", "completed"),
            timestamp=datetime.utcnow()
        )
        self._session.add(usage)
        await self._session.commit()
        await self._session.refresh(usage)
        return usage

    async def get_model_usage_stats(self, model_id: int, start_date: Optional[datetime] = None) -> List[AIUsage]:
        """Get usage statistics for a model."""
        query = select(AIUsage).where(AIUsage.model_id == model_id)
        if start_date:
            query = query.where(AIUsage.timestamp >= start_date)
        usage_stats = await self._session.execute(query)
        return usage_stats.scalars().all()

    async def deactivate_model(self, model_id: int) -> AIModel:
        """Deactivate an AI model."""
        model = await self.get_model(model_id)
        model.status = "inactive"
        await self._session.commit()
        await self._session.refresh(model)
        return model

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from Backend.data_layer.database.models.ai_models import AIModel
from datetime import datetime


class AIModelRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_model(self, model_data: Dict[str, Any]) -> AIModel:
        """Create a new AI model."""
        model = AIModel(
            name=model_data["name"],
            version=model_data.get("version"),
            type=model_data.get("type"),
            storage_path=model_data.get("storage_path"),
            model_metadata=model_data.get("model_metadata", {}),
            status=model_data.get("status", "active"),
            provider=model_data.get("provider"),
            api_key_reference=model_data.get("api_key_reference"),
            max_tokens=model_data.get("max_tokens"),
            temperature=model_data.get("temperature"),
            cost_per_request=model_data.get("cost_per_request", 0.0),
            total_requests=0,
            average_latency=0.0
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def get_model(self, model_id: int) -> Optional[AIModel]:
        """Get an AI model by ID."""
        query = select(AIModel).where(AIModel.id == model_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_model_by_name_version(self, name: str, version: str) -> Optional[AIModel]:
        """Get an AI model by name and version."""
        query = select(AIModel).where(
            AIModel.name == name,
            AIModel.version == version
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_models(
        self,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        type: Optional[str] = None
    ) -> List[AIModel]:
        """List AI models with optional filters."""
        query = select(AIModel)

        if provider:
            query = query.where(AIModel.provider == provider)
        if status:
            query = query.where(AIModel.status == status)
        if type:
            query = query.where(AIModel.type == type)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_model(self, model_id: int, model_data: Dict[str, Any]) -> Optional[AIModel]:
        """Update an AI model."""
        model = await self.get_model(model_id)
        if not model:
            return None

        update_data = {
            key: value for key, value in model_data.items()
            if hasattr(model, key) and value is not None
        }

        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            query = (
                update(AIModel)
                .where(AIModel.id == model_id)
                .values(**update_data)
            )
            await self.session.execute(query)
            await self.session.commit()
            await self.session.refresh(model)

        return model

    async def delete_model(self, model_id: int) -> bool:
        """Delete an AI model."""
        model = await self.get_model(model_id)
        if not model:
            return False

        query = delete(AIModel).where(AIModel.id == model_id)
        await self.session.execute(query)
        await self.session.commit()
        return True

    async def update_model_stats(
        self,
        model_id: int,
        latency: float,
        success: bool = True
    ) -> Optional[AIModel]:
        """Update model usage statistics."""
        model = await self.get_model(model_id)
        if not model:
            return None

        # Update statistics
        total_requests = model.total_requests + 1
        new_average_latency = (
            (model.average_latency * model.total_requests + latency) / total_requests
            if model.total_requests > 0
            else latency
        )

        update_data = {
            "total_requests": total_requests,
            "average_latency": new_average_latency,
            "last_used": datetime.utcnow()
        }

        query = (
            update(AIModel)
            .where(AIModel.id == model_id)
            .values(**update_data)
        )
        await self.session.execute(query)
        await self.session.commit()
        await self.session.refresh(model)

        return model

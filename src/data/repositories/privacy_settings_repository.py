"""Privacy settings repository module."""
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.privacy_settings import PrivacySettings
from core.exceptions import PrivacySettingsNotFoundError

class PrivacySettingsRepository:
    """Repository for managing privacy settings."""

    def __init__(self, session: AsyncSession):
        """Initialize privacy settings repository."""
        self._session = session

    async def get_settings(self, user_id: int) -> PrivacySettings:
        """Get privacy settings for a user."""
        settings = await self._session.execute(
            select(PrivacySettings).where(PrivacySettings.user_id == user_id)
        )
        settings = settings.scalar_one_or_none()
        if not settings:
            raise PrivacySettingsNotFoundError(
                f"Privacy settings for user {user_id} not found"
            )
        return settings

    async def create_settings(self, settings_data: Dict) -> PrivacySettings:
        """Create privacy settings."""
        settings = PrivacySettings(
            user_id=settings_data["user_id"],
            data_collection=settings_data.get("data_collection", True),
            data_sharing=settings_data.get("data_sharing", False),
            marketing_communications=settings_data.get("marketing_communications", False),
            analytics_tracking=settings_data.get("analytics_tracking", True),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self._session.add(settings)
        await self._session.commit()
        await self._session.refresh(settings)
        return settings

    async def update_settings(
        self,
        user_id: int,
        settings_data: Dict
    ) -> PrivacySettings:
        """Update privacy settings."""
        settings = await self.get_settings(user_id)
        for key, value in settings_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        settings.updated_at = datetime.utcnow()
        await self._session.commit()
        await self._session.refresh(settings)
        return settings

    async def delete_settings(self, user_id: int) -> None:
        """Delete privacy settings."""
        settings = await self.get_settings(user_id)
        await self._session.delete(settings)
        await self._session.commit()

    async def get_or_create_settings(self, user_id: int) -> PrivacySettings:
        """Get existing settings or create new ones with defaults."""
        try:
            return await self.get_settings(user_id)
        except PrivacySettingsNotFoundError:
            return await self.create_settings({"user_id": user_id})

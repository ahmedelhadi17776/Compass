"""User preferences repository module."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.user_preferences import UserPreferences
from core.exceptions import PreferencesNotFoundError

class UserPreferencesRepository:
    """User preferences repository class."""

    def __init__(self, session: AsyncSession):
        """Initialize user preferences repository."""
        self._session = session

    async def get_preferences(self, user_id: int) -> UserPreferences:
        """Get user preferences."""
        preferences = await self._session.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        preferences = preferences.scalar_one_or_none()
        if not preferences:
            raise PreferencesNotFoundError(f"Preferences for user {user_id} not found")
        return preferences

    async def create_preferences(self, preferences_data: dict) -> UserPreferences:
        """Create user preferences."""
        preferences = UserPreferences(**preferences_data)
        self._session.add(preferences)
        await self._session.commit()
        await self._session.refresh(preferences)
        return preferences

    async def update_preferences(self, user_id: int, preferences_data: dict) -> UserPreferences:
        """Update user preferences."""
        preferences = await self.get_preferences(user_id)
        for key, value in preferences_data.items():
            if hasattr(preferences, key) and value is not None:
                setattr(preferences, key, value)
        await self._session.commit()
        await self._session.refresh(preferences)
        return preferences

    async def get_or_create_preferences(self, user_id: int) -> UserPreferences:
        """Get existing preferences or create new ones."""
        try:
            return await self.get_preferences(user_id)
        except PreferencesNotFoundError:
            return await self.create_preferences({"user_id": user_id})

    async def update_theme_preferences(
        self, user_id: int, theme: str, dark_mode: bool
    ) -> UserPreferences:
        """Update theme preferences."""
        return await self.update_preferences(
            user_id, {"theme": theme, "dark_mode": dark_mode}
        )

    async def update_notification_preferences(
        self, user_id: int, email_notifications: bool, push_notifications: bool
    ) -> UserPreferences:
        """Update notification preferences."""
        return await self.update_preferences(
            user_id,
            {
                "email_notifications": email_notifications,
                "push_notifications": push_notifications,
            }
        )

    async def update_accessibility_settings(
        self, user_id: int, font_size: str, high_contrast: bool
    ) -> UserPreferences:
        """Update accessibility settings."""
        return await self.update_preferences(
            user_id,
            {
                "font_size": font_size,
                "high_contrast": high_contrast,
            }
        )

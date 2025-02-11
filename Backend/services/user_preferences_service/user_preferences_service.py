"""User preferences service module."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ...data.repositories.user_preferences_repository import UserPreferencesRepository
from ...data.database.models.user_preferences import UserPreferences
from core.exceptions import PreferencesNotFoundError

class UserPreferencesService:
    """User preferences service class."""

    def __init__(self, session: AsyncSession):
        """Initialize user preferences service."""
        self._repository = UserPreferencesRepository(session)

    async def get_user_preferences(self, user_id: int) -> UserPreferences:
        """Get user preferences, creating default ones if they don't exist."""
        try:
            return await self._repository.get_preferences(user_id)
        except PreferencesNotFoundError:
            return await self.create_default_preferences(user_id)

    async def create_default_preferences(self, user_id: int) -> UserPreferences:
        """Create default preferences for a user."""
        default_preferences = {
            "user_id": user_id,
            "theme": "light",
            "dark_mode": False,
            "font_size": "medium",
            "email_notifications": True,
            "push_notifications": True,
            "high_contrast": False,
            "language": "en"
        }
        return await self._repository.create_preferences(default_preferences)

    async def update_theme_settings(
        self, user_id: int, theme: str, dark_mode: bool
    ) -> UserPreferences:
        """Update user's theme settings."""
        # Validate theme
        valid_themes = ["light", "dark", "system", "custom"]
        if theme not in valid_themes:
            raise ValueError(f"Invalid theme. Must be one of: {valid_themes}")

        return await self._repository.update_theme_preferences(user_id, theme, dark_mode)

    async def update_notification_settings(
        self,
        user_id: int,
        email_notifications: bool,
        push_notifications: bool
    ) -> UserPreferences:
        """Update user's notification settings."""
        return await self._repository.update_notification_preferences(
            user_id,
            email_notifications,
            push_notifications
        )

    async def update_accessibility_settings(
        self,
        user_id: int,
        font_size: str,
        high_contrast: bool
    ) -> UserPreferences:
        """Update user's accessibility settings."""
        # Validate font size
        valid_font_sizes = ["small", "medium", "large", "x-large"]
        if font_size not in valid_font_sizes:
            raise ValueError(f"Invalid font size. Must be one of: {valid_font_sizes}")

        return await self._repository.update_accessibility_settings(
            user_id,
            font_size,
            high_contrast
        )

    async def update_language_preference(
        self, user_id: int, language: str
    ) -> UserPreferences:
        """Update user's language preference."""
        # Validate language code
        # In a real application, you would have a more comprehensive list
        valid_languages = ["en", "es", "fr", "de", "ar"]
        if language not in valid_languages:
            raise ValueError(f"Invalid language code. Must be one of: {valid_languages}")

        return await self._repository.update_preferences(
            user_id,
            {"language": language}
        )

    async def bulk_update_preferences(
        self, user_id: int, preferences_data: dict
    ) -> UserPreferences:
        """Update multiple preferences at once."""
        # Validate theme if present
        if "theme" in preferences_data:
            valid_themes = ["light", "dark", "system", "custom"]
            if preferences_data["theme"] not in valid_themes:
                raise ValueError(f"Invalid theme. Must be one of: {valid_themes}")

        # Validate font size if present
        if "font_size" in preferences_data:
            valid_font_sizes = ["small", "medium", "large", "x-large"]
            if preferences_data["font_size"] not in valid_font_sizes:
                raise ValueError(f"Invalid font size. Must be one of: {valid_font_sizes}")

        # Validate language if present
        if "language" in preferences_data:
            valid_languages = ["en", "es", "fr", "de", "ar"]
            if preferences_data["language"] not in valid_languages:
                raise ValueError(f"Invalid language code. Must be one of: {valid_languages}")

        return await self._repository.update_preferences(user_id, preferences_data)

    async def reset_preferences(self, user_id: int) -> UserPreferences:
        """Reset user preferences to default values."""
        try:
            current_preferences = await self._repository.get_preferences(user_id)
            return await self.bulk_update_preferences(
                user_id,
                {
                    "theme": "light",
                    "dark_mode": False,
                    "font_size": "medium",
                    "email_notifications": True,
                    "push_notifications": True,
                    "high_contrast": False,
                    "language": "en"
                }
            )
        except PreferencesNotFoundError:
            return await self.create_default_preferences(user_id)

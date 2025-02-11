"""Repository for User Preferences related database operations."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.user_preferences import UserPreference, UserSetting
from .base_repository import BaseRepository

class UserPreferenceRepository(BaseRepository[UserPreference]):
    """Repository for User Preference operations."""

    def __init__(self, session: Session):
        super().__init__(UserPreference, session)

    def get_by_user(self, user_id: int) -> Optional[UserPreference]:
        """Get preferences for a specific user."""
        return self.session.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()

    def update_theme(self, user_id: int, theme: str) -> Optional[UserPreference]:
        """Update user's theme preference."""
        pref = self.get_by_user(user_id)
        if pref:
            pref.theme = theme
            self.session.commit()
        return pref

class UserSettingRepository(BaseRepository[UserSetting]):
    """Repository for User Setting operations."""

    def __init__(self, session: Session):
        super().__init__(UserSetting, session)

    def get_user_settings(self, user_id: int) -> List[UserSetting]:
        """Get all settings for a specific user."""
        return self.session.query(UserSetting).filter(
            UserSetting.user_id == user_id
        ).all()

    def get_setting(self, user_id: int, setting_key: str) -> Optional[UserSetting]:
        """Get specific setting for a user."""
        return self.session.query(UserSetting).filter(
            and_(
                UserSetting.user_id == user_id,
                UserSetting.setting_key == setting_key
            )
        ).first()

    def update_setting(self, user_id: int, setting_key: str, setting_value: dict) -> Optional[UserSetting]:
        """Update or create user setting."""
        setting = self.get_setting(user_id, setting_key)
        if setting:
            setting.setting_value = setting_value
        else:
            setting = UserSetting(
                user_id=user_id,
                setting_key=setting_key,
                setting_value=setting_value
            )
            self.session.add(setting)
        self.session.commit()
        return setting

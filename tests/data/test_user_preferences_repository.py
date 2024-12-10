"""Test user preferences repository."""
import pytest
from datetime import datetime

from src.data.repositories.user_preferences_repository import UserPreferencesRepository
from src.data.database.models.user_preferences import UserPreferences
from core.exceptions import PreferencesNotFoundError

@pytest.mark.asyncio
async def test_create_preferences(test_db):
    """Test creating user preferences."""
    repository = UserPreferencesRepository(test_db)
    preferences_data = {
        "user_id": 1,
        "theme": "light",
        "dark_mode": False,
        "font_size": "medium",
        "email_notifications": True,
        "push_notifications": True,
        "high_contrast": False
    }

    preferences = await repository.create_preferences(preferences_data)
    assert preferences.user_id == preferences_data["user_id"]
    assert preferences.theme == preferences_data["theme"]
    assert preferences.dark_mode == preferences_data["dark_mode"]
    assert preferences.font_size == preferences_data["font_size"]

@pytest.mark.asyncio
async def test_get_preferences(test_db):
    """Test getting user preferences."""
    repository = UserPreferencesRepository(test_db)
    preferences_data = {
        "user_id": 1,
        "theme": "dark",
        "dark_mode": True,
        "font_size": "large"
    }
    preferences = UserPreferences(**preferences_data)
    test_db.add(preferences)
    await test_db.commit()

    retrieved_preferences = await repository.get_preferences(preferences_data["user_id"])
    assert retrieved_preferences.theme == preferences_data["theme"]
    assert retrieved_preferences.dark_mode == preferences_data["dark_mode"]
    assert retrieved_preferences.font_size == preferences_data["font_size"]

@pytest.mark.asyncio
async def test_get_preferences_not_found(test_db):
    """Test getting non-existent preferences."""
    repository = UserPreferencesRepository(test_db)
    with pytest.raises(PreferencesNotFoundError):
        await repository.get_preferences(999)

@pytest.mark.asyncio
async def test_update_preferences(test_db):
    """Test updating user preferences."""
    repository = UserPreferencesRepository(test_db)
    preferences_data = {
        "user_id": 1,
        "theme": "light",
        "dark_mode": False
    }
    preferences = UserPreferences(**preferences_data)
    test_db.add(preferences)
    await test_db.commit()

    update_data = {
        "theme": "dark",
        "dark_mode": True
    }
    updated_preferences = await repository.update_preferences(preferences_data["user_id"], update_data)
    assert updated_preferences.theme == update_data["theme"]
    assert updated_preferences.dark_mode == update_data["dark_mode"]

@pytest.mark.asyncio
async def test_get_or_create_preferences(test_db):
    """Test getting or creating preferences."""
    repository = UserPreferencesRepository(test_db)
    user_id = 1

    # First call should create new preferences
    preferences = await repository.get_or_create_preferences(user_id)
    assert preferences.user_id == user_id

    # Second call should return existing preferences
    same_preferences = await repository.get_or_create_preferences(user_id)
    assert same_preferences.id == preferences.id

@pytest.mark.asyncio
async def test_update_theme_preferences(test_db):
    """Test updating theme preferences."""
    repository = UserPreferencesRepository(test_db)
    preferences_data = {
        "user_id": 1,
        "theme": "light",
        "dark_mode": False
    }
    preferences = UserPreferences(**preferences_data)
    test_db.add(preferences)
    await test_db.commit()

    updated_preferences = await repository.update_theme_preferences(
        preferences_data["user_id"],
        theme="dark",
        dark_mode=True
    )
    assert updated_preferences.theme == "dark"
    assert updated_preferences.dark_mode == True

@pytest.mark.asyncio
async def test_update_notification_preferences(test_db):
    """Test updating notification preferences."""
    repository = UserPreferencesRepository(test_db)
    preferences_data = {
        "user_id": 1,
        "email_notifications": True,
        "push_notifications": True
    }
    preferences = UserPreferences(**preferences_data)
    test_db.add(preferences)
    await test_db.commit()

    updated_preferences = await repository.update_notification_preferences(
        preferences_data["user_id"],
        email_notifications=False,
        push_notifications=False
    )
    assert updated_preferences.email_notifications == False
    assert updated_preferences.push_notifications == False

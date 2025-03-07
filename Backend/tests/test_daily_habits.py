import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.data_layer.database.models.daily_habits import DailyHabit
from Backend.data_layer.repositories.daily_habits_repository import DailyHabitRepository
from Backend.services.daily_habits_service import DailyHabitService
from Backend.main import app
from Backend.data_layer.database.connection import get_db
from sqlalchemy.future import select


# Test user ID for all tests
TEST_USER_ID = 1


@pytest.fixture
async def db_session():
    """Get a test database session."""
    async for session in get_db():
        yield session


@pytest.fixture
async def client():
    """Get a test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def repository(db_session):
    """Get a test repository instance."""
    return DailyHabitRepository(db_session)


@pytest.fixture
async def service(repository):
    """Get a test service instance."""
    return DailyHabitService(repository)


@pytest.fixture
async def test_habit(db_session):
    """Create a test habit for testing."""
    habit = DailyHabit(
        user_id=TEST_USER_ID,
        habit_name="Test Habit",
        description="A test habit for testing",
        start_day=date.today() - timedelta(days=7),
        end_day=date.today() + timedelta(days=30),
        current_streak=0,
        longest_streak=0,
        is_completed=False
    )
    db_session.add(habit)
    await db_session.flush()
    await db_session.commit()

    # Refresh to get the ID
    await db_session.refresh(habit)

    yield habit

    # Cleanup
    await db_session.delete(habit)
    await db_session.commit()


# Repository Tests
class TestDailyHabitRepository:

    async def test_create_habit(self, repository, db_session):
        """Test creating a new habit."""
        habit_data = {
            "user_id": TEST_USER_ID,
            "habit_name": "Morning Meditation",
            "description": "Meditate for 10 minutes every morning",
            "start_day": date.today(),
            "end_day": date.today() + timedelta(days=30)
        }

        habit = await repository.create(**habit_data)
        assert habit is not None
        assert habit.id is not None
        assert habit.habit_name == "Morning Meditation"
        assert habit.current_streak == 0
        assert habit.is_completed is False

        # Cleanup
        await db_session.delete(habit)
        await db_session.commit()

    async def test_get_by_id(self, repository, test_habit):
        """Test getting a habit by ID."""
        habit = await repository.get_by_id(test_habit.id, TEST_USER_ID)
        assert habit is not None
        assert habit.id == test_habit.id
        assert habit.habit_name == test_habit.habit_name

    async def test_get_user_habits(self, repository, test_habit):
        """Test getting all habits for a user."""
        habits = await repository.get_user_habits(TEST_USER_ID)
        assert len(habits) >= 1
        assert any(h.id == test_habit.id for h in habits)

    async def test_update_habit(self, repository, test_habit):
        """Test updating a habit."""
        updated = await repository.update(
            test_habit.id,
            TEST_USER_ID,
            habit_name="Updated Habit Name"
        )
        assert updated is not None
        assert updated.habit_name == "Updated Habit Name"

    async def test_mark_habit_completed(self, repository, test_habit):
        """Test marking a habit as completed."""
        # Ensure habit is not completed initially
        assert test_habit.is_completed is False
        assert test_habit.current_streak == 0

        # Mark as completed
        updated = await repository.mark_habit_completed(test_habit.id, TEST_USER_ID)
        assert updated is not None
        assert updated.is_completed is True
        assert updated.current_streak == 1
        assert updated.last_completed_date == date.today()

    async def test_streak_increment(self, repository, test_habit, db_session):
        """Test that streak increments correctly on consecutive days."""
        # Set up: Mark as completed yesterday
        yesterday = date.today() - timedelta(days=1)
        test_habit.mark_completed(yesterday)
        test_habit.is_completed = False  # Reset completion status for today
        await db_session.commit()

        # Mark as completed today
        updated = await repository.mark_habit_completed(test_habit.id, TEST_USER_ID)
        # Should be 2 now (yesterday + today)
        assert updated.current_streak == 2
        assert updated.longest_streak == 2

    async def test_streak_reset(self, repository, test_habit, db_session):
        """Test that streak resets when a day is missed."""
        # Set up: Mark as completed 2 days ago
        two_days_ago = date.today() - timedelta(days=2)
        test_habit.mark_completed(two_days_ago)
        test_habit.is_completed = False  # Reset completion status
        await db_session.commit()

        # Mark as completed today (skipping yesterday)
        updated = await repository.mark_habit_completed(test_habit.id, TEST_USER_ID)
        assert updated.current_streak == 1  # Should reset to 1 since yesterday was missed

    async def test_reset_daily_completions(self, repository, test_habit, db_session):
        """Test resetting daily completions."""
        # Mark habit as completed
        test_habit.is_completed = True
        await db_session.commit()

        # Reset completions
        reset_count = await repository.reset_daily_completions()
        assert reset_count >= 1

        # Verify habit is no longer completed
        result = await db_session.execute(select(DailyHabit).where(DailyHabit.id == test_habit.id))
        habit = result.scalars().first()
        assert habit.is_completed is False


# Service Tests
class TestDailyHabitService:

    async def test_create_habit(self, service, db_session):
        """Test creating a habit through the service."""
        habit_data = {
            "user_id": TEST_USER_ID,
            "habit_name": "Evening Reading",
            "description": "Read for 30 minutes before bed",
            "start_day": date.today(),
            "end_day": date.today() + timedelta(days=30)
        }

        habit = await service.create_habit(**habit_data)
        assert habit is not None
        assert habit.id is not None
        assert habit.habit_name == "Evening Reading"

        # Cleanup
        await db_session.delete(habit)
        await db_session.commit()

    async def test_get_habit_by_id(self, service, test_habit):
        """Test getting a habit by ID through the service."""
        habit = await service.get_habit_by_id(test_habit.id, TEST_USER_ID)
        assert habit is not None
        assert habit.id == test_habit.id

    async def test_mark_habit_completed(self, service, test_habit):
        """Test marking a habit as completed through the service."""
        habit = await service.mark_habit_completed(test_habit.id, TEST_USER_ID)
        assert habit is not None
        assert habit.is_completed is True
        assert habit.current_streak == 1

    async def test_process_daily_reset(self, service, test_habit, db_session):
        """Test the daily reset process."""
        # Mark habit as completed
        test_habit.is_completed = True
        await db_session.commit()

        # Process daily reset
        result = await service.process_daily_reset()
        assert "completions_reset" in result
        assert result["completions_reset"] >= 1

        # Verify habit is no longer completed
        result = await db_session.execute(select(DailyHabit).where(DailyHabit.id == test_habit.id))
        habit = result.scalars().first()
        assert habit.is_completed is False


# API Tests
class TestDailyHabitAPI:

    async def test_create_habit_api(self, client):
        """Test creating a habit through the API."""
        habit_data = {
            "user_id": TEST_USER_ID,
            "habit_name": "API Test Habit",
            "description": "Testing habit creation via API",
            "start_day": date.today().isoformat(),
            "end_day": (date.today() + timedelta(days=30)).isoformat()
        }

        response = await client.post("/daily-habits/", json=habit_data)
        assert response.status_code == 201
        data = response.json()
        assert data["habit_name"] == "API Test Habit"
        assert data["user_id"] == TEST_USER_ID

        # Cleanup - delete the created habit
        habit_id = data["id"]
        await client.delete(f"/daily-habits/{habit_id}?user_id={TEST_USER_ID}")

    async def test_get_habit_api(self, client, test_habit):
        """Test getting a habit through the API."""
        response = await client.get(f"/daily-habits/{test_habit.id}?user_id={TEST_USER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_habit.id
        assert data["habit_name"] == test_habit.habit_name

    async def test_get_user_habits_api(self, client, test_habit):
        """Test getting all habits for a user through the API."""
        response = await client.get(f"/daily-habits/user/{TEST_USER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(h["id"] == test_habit.id for h in data)

    async def test_update_habit_api(self, client, test_habit):
        """Test updating a habit through the API."""
        update_data = {
            "habit_name": "Updated API Habit",
            "description": "Updated via API test"
        }

        response = await client.put(
            f"/daily-habits/{test_habit.id}?user_id={TEST_USER_ID}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["habit_name"] == "Updated API Habit"
        assert data["description"] == "Updated via API test"

    async def test_mark_habit_completed_api(self, client, test_habit):
        """Test marking a habit as completed through the API."""
        response = await client.post(f"/daily-habits/{test_habit.id}/complete?user_id={TEST_USER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["is_completed"] is True
        assert data["current_streak"] >= 1

    async def test_delete_habit_api(self, client, db_session):
        """Test deleting a habit through the API."""
        # Create a habit to delete
        habit = DailyHabit(
            user_id=TEST_USER_ID,
            habit_name="Habit to Delete",
            description="This habit will be deleted",
            start_day=date.today(),
            end_day=date.today() + timedelta(days=30)
        )
        db_session.add(habit)
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(habit)

        # Delete the habit
        response = await client.delete(f"/daily-habits/{habit.id}?user_id={TEST_USER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Habit deleted successfully"

        # Verify it's gone
        result = await db_session.execute(select(DailyHabit).where(DailyHabit.id == habit.id))
        deleted_habit = result.scalars().first()
        assert deleted_habit is None

    async def test_process_daily_reset_api(self, client, test_habit, db_session):
        """Test the daily reset process through the API."""
        # Mark habit as completed
        test_habit.is_completed = True
        await db_session.commit()

        # Trigger daily reset
        response = await client.post("/daily-habits/process-daily-reset")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Daily reset process started"

        # Give the background task time to complete
        await asyncio.sleep(1)

        # Verify habit is no longer completed
        result = await db_session.execute(select(DailyHabit).where(DailyHabit.id == test_habit.id))
        habit = result.scalars().first()
        assert habit.is_completed is False

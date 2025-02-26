import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from Backend.data_layer.database.models.todo import Todo, TodoPriority, TodoStatus
from Backend.services.todo_service import TodoService
from Backend.data_layer.repositories.todo_repository import TodoRepository
import logging
from typing import Dict, Any, AsyncGenerator, Optional
import asyncio

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture
async def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Clean up any pending tasks
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    await loop.shutdown_asyncgens()
    loop.close()


@pytest.fixture
async def redis_client():
    """Create a mock Redis client for testing."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = True

    with patch('Backend.data_layer.cache.redis_client.redis_client', mock_redis):
        yield mock_redis


@pytest.fixture
async def mock_repository():
    """Create a mock repository with async methods."""
    repository = AsyncMock(spec=TodoRepository)
    repository.create.return_value = None
    repository.get_by_id.return_value = None
    repository.update.return_value = None
    repository.delete.return_value = None
    repository.get_all.return_value = []
    return repository


@pytest.fixture
def mock_todo_dict():
    """Create a mock todo dictionary."""
    now = datetime.now()
    return {
        "id": 1,
        "user_id": 1,
        "title": "Test Todo",
        "description": "Test Description",
        "status": "pending",  # Use string instead of enum for JSON serialization
        "priority": "medium",  # Use string instead of enum for JSON serialization
        "due_date": None,
        "reminder_time": None,
        "is_recurring": False,
        "linked_task_id": None,
        "linked_calendar_event_id": None,
        "ai_generated": False,
        "created_at": now,  # Use actual datetime object
        "updated_at": now,  # Use actual datetime object
        "_completion_date": None
    }


@pytest.fixture
def mock_todo(mock_todo_dict):
    """Create a mock todo object that can be serialized to JSON."""
    todo = MagicMock(spec=Todo)
    for key, value in mock_todo_dict.items():
        setattr(todo, key, value)

    # Add dictionary representation for JSON serialization
    def to_dict():
        return {
            'id': todo.id,
            'user_id': todo.user_id,
            'title': todo.title,
            'description': todo.description,
            'status': todo.status,
            'priority': todo.priority,
            'due_date': todo.due_date.isoformat() if todo.due_date else None,
            'is_recurring': todo.is_recurring,
            'created_at': todo.created_at.isoformat() if todo.created_at else None,
            'updated_at': todo.updated_at.isoformat() if todo.updated_at else None
        }

    todo.to_dict = to_dict
    todo.__dict__.update(mock_todo_dict)
    return todo


@pytest.mark.asyncio
async def test_create_todo(mock_repository: AsyncMock, mock_todo: MagicMock, mock_todo_dict):
    """Test creating a todo."""
    mock_repository.create.return_value = mock_todo
    service = TodoService(mock_repository)

    with patch('Backend.services.todo_service.create_todo_task', new_callable=AsyncMock) as mock_create_task:
        mock_create_task.return_value = mock_todo
        result = await service.create_todo(**mock_todo_dict)

        assert result == mock_todo
        mock_create_task.assert_called_once_with(mock_todo_dict)


@pytest.mark.asyncio
async def test_get_todo_by_id(mock_repository: AsyncMock, mock_todo: MagicMock, redis_client: AsyncMock):
    """Test getting a todo by ID."""
    with patch('Backend.services.todo_service.get_todo_by_id', new_callable=AsyncMock) as mock_get_task:
        mock_get_task.return_value = mock_todo
        service = TodoService(mock_repository)

        result = await service.get_todo_by_id(todo_id=1, user_id=1)

        assert result == mock_todo
        mock_get_task.assert_called_once_with(1, 1)


@pytest.mark.asyncio
async def test_update_todo(mock_repository: AsyncMock, mock_todo: MagicMock, redis_client: AsyncMock):
    """Test updating a todo."""
    update_data = {"title": "Updated Title"}

    with patch('Backend.services.todo_service.update_todo_task', new_callable=AsyncMock) as mock_update_task:
        mock_update_task.return_value = mock_todo
        service = TodoService(mock_repository)

        result = await service.update_todo(todo_id=1, user_id=1, **update_data)

        assert result == mock_todo
        mock_update_task.assert_called_once_with(1, 1, update_data)
        # Verify that all three cache keys are invalidated
        assert redis_client.delete.call_count == 3
        redis_client.delete.assert_any_call("user_todos:1:all")
        redis_client.delete.assert_any_call("user_todos:1:pending")
        redis_client.delete.assert_any_call("user_todos:1:completed")


@pytest.mark.asyncio
async def test_get_user_todos(mock_repository: AsyncMock, mock_todo: MagicMock, redis_client: AsyncMock):
    """Test getting todos for a user."""
    with patch('Backend.services.todo_service.get_todos', new_callable=AsyncMock) as mock_get_todos:
        mock_get_todos.return_value = [mock_todo]
        service = TodoService(mock_repository)

        result = await service.get_user_todos(user_id=1)

        assert result == [mock_todo]
        mock_get_todos.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_delete_todo(mock_repository: AsyncMock, mock_todo: MagicMock, redis_client: AsyncMock):
    """Test deleting a todo."""
    with patch('Backend.services.todo_service.delete_todo_task', new_callable=AsyncMock) as mock_delete_task:
        mock_delete_task.return_value = True
        service = TodoService(mock_repository)

        result = await service.delete_todo(todo_id=1, user_id=1)

        assert result is True
        mock_delete_task.assert_called_once_with(1, 1)
        # Verify that all three cache keys are invalidated
        assert redis_client.delete.call_count == 3
        redis_client.delete.assert_any_call("user_todos:1:all")
        redis_client.delete.assert_any_call("user_todos:1:pending")
        redis_client.delete.assert_any_call("user_todos:1:completed")


@pytest.mark.asyncio
async def test_todo_not_found(mock_repository: AsyncMock, redis_client: AsyncMock):
    """Test handling when a todo is not found."""
    with patch('Backend.services.todo_service.get_todo_by_id', new_callable=AsyncMock) as mock_get_task:
        mock_get_task.return_value = None
        service = TodoService(mock_repository)

        result = await service.get_todo_by_id(todo_id=1, user_id=1)

        assert result is None
        mock_get_task.assert_called_once_with(1, 1)


@pytest.mark.asyncio
async def test_update_todo_not_found(mock_repository: AsyncMock):
    """Test handling when updating a non-existent todo."""
    with patch('Backend.services.todo_service.update_todo_task', new_callable=AsyncMock) as mock_update_task:
        mock_update_task.return_value = None
        service = TodoService(mock_repository)

        result = await service.update_todo(todo_id=1, user_id=1, title="Updated")

        assert result is None
        mock_update_task.assert_called_once_with(1, 1, {"title": "Updated"})

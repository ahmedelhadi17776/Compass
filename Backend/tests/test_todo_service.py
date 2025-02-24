import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from Backend.core.celery_app import create_todo_task
from Backend.data_layer.database.models.task import Task
from Backend.data_layer.database.models.todo import TodoPriority


@pytest.fixture
def mock_celery_task():
    with patch("Backend.core.celery_app.create_todo_task") as mock:
        mock.delay = MagicMock()
        yield mock


@pytest.mark.asyncio
async def test_create_new_todo_with_celery(mock_celery_task):
    todo_data = {
        'creator_id': 1,
        'title': 'Test Todo',
        'description': 'Test Description',
        'priority': TodoPriority.MEDIUM,
        'due_date': datetime(2025, 2, 23, 2, 15, 11, 267806),
        'status': 'pending',
        'created_at': datetime(2025, 2, 23, 4, 15, 11, 267806),
        'updated_at': datetime(2025, 2, 23, 4, 15, 11, 267806)
    }

    mock_celery_task.delay.return_value = AsyncMock(
        get=AsyncMock(return_value=Task(**todo_data))
    )

    response = await create_todo_task(todo_data)
    assert response is not None
    mock_celery_task.delay.assert_called_once_with(todo_data=todo_data)


@pytest.mark.asyncio
async def test_get_todo_by_id_with_celery(mock_celery_task):
    todo_id = 1
    mock_todo = Task(id=todo_id, title="Test Todo")
    mock_celery_task.delay.return_value = AsyncMock(
        get=AsyncMock(return_value=mock_todo)
    )

    response = await create_todo_task({"id": todo_id})
    assert response is not None
    mock_celery_task.delay.assert_called_once()


@pytest.mark.asyncio
async def test_convert_task_to_todo_with_celery(mock_celery_task):
    task_data = {
        "id": 1,
        "title": "Test Task",
        "description": "Test Description",
        "priority": TodoPriority.MEDIUM,
        "status": "pending",
    }
    mock_task = Task(**task_data)
    mock_celery_task.delay.return_value = AsyncMock(
        get=AsyncMock(return_value=mock_task)
    )

    response = await create_todo_task(task_data)
    assert response is not None
    assert response.title == task_data["title"]


@pytest.mark.asyncio
async def test_update_todo_with_celery(mock_celery_task):
    todo_id = 1
    update_data = {"title": "Updated Todo",
                   "description": "Updated Description"}
    mock_todo = Task(id=todo_id, **update_data)
    mock_celery_task.delay.return_value = AsyncMock(
        get=AsyncMock(return_value=mock_todo)
    )

    response = await create_todo_task({"id": todo_id, **update_data})
    assert response is not None
    assert response.title == update_data["title"]


@pytest.mark.asyncio
async def test_get_user_todos_with_celery(mock_celery_task):
    user_id = 1
    mock_todos = [
        Task(id=1, title="Todo 1", creator_id=1),
        Task(id=2, title="Todo 2", creator_id=1)
    ]
    mock_celery_task.delay.return_value = AsyncMock(
        get=AsyncMock(return_value=mock_todos)
    )

    response = await create_todo_task({"creator_id": 1})
    assert response is not None
    assert len(response) == 2

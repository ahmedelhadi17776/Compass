"""Test task repository."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.data.repositories.task_repository import TaskRepository
from Backend.data.database.models.task import Task
from core.exceptions import TaskNotFoundError

@pytest.mark.asyncio
async def test_create_task(test_db: AsyncSession):
    """Test creating a task."""
    repository = TaskRepository(test_db)
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "priority": "high",
        "status": "pending"
    }
    user_id = 1

    task = await repository.create_task(task_data, user_id)
    assert task.title == task_data["title"]
    assert task.description == task_data["description"]
    assert task.user_id == user_id

@pytest.mark.asyncio
async def test_get_task(test_db: AsyncSession):
    """Test getting a task."""
    repository = TaskRepository(test_db)
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "user_id": 1
    }
    task = Task(**task_data)
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)

    retrieved_task = await repository.get_task(task.id, task_data["user_id"])
    assert retrieved_task.title == task_data["title"]
    assert retrieved_task.description == task_data["description"]

@pytest.mark.asyncio
async def test_get_task_not_found(test_db: AsyncSession):
    """Test getting a non-existent task."""
    repository = TaskRepository(test_db)
    with pytest.raises(TaskNotFoundError):
        await repository.get_task(999, 1)

@pytest.mark.asyncio
async def test_get_user_tasks(test_db: AsyncSession):
    """Test getting all tasks for a user."""
    repository = TaskRepository(test_db)
    user_id = 1
    tasks_data = [
        {"title": "Task 1", "user_id": user_id},
        {"title": "Task 2", "user_id": user_id},
        {"title": "Task 3", "user_id": 2}  # Different user
    ]
    
    for task_data in tasks_data:
        test_db.add(Task(**task_data))
    await test_db.commit()

    user_tasks = await repository.get_user_tasks(user_id)
    assert len(user_tasks) == 2
    assert all(task.user_id == user_id for task in user_tasks)

@pytest.mark.asyncio
async def test_update_task(test_db: AsyncSession):
    """Test updating a task."""
    repository = TaskRepository(test_db)
    task = Task(title="Original Title", user_id=1)
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)

    update_data = {"title": "Updated Title"}
    updated_task = await repository.update_task(task.id, 1, update_data)
    assert updated_task.title == "Updated Title"

@pytest.mark.asyncio
async def test_delete_task(test_db: AsyncSession):
    """Test deleting a task."""
    repository = TaskRepository(test_db)
    task = Task(title="Test Task", user_id=1)
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)

    await repository.delete_task(task.id, 1)
    with pytest.raises(TaskNotFoundError):
        await repository.get_task(task.id, 1)

@pytest.mark.asyncio
async def test_get_tasks_by_status(test_db: AsyncSession):
    """Test getting tasks by status."""
    repository = TaskRepository(test_db)
    user_id = 1
    tasks_data = [
        {"title": "Task 1", "user_id": user_id, "status": "pending"},
        {"title": "Task 2", "user_id": user_id, "status": "completed"},
        {"title": "Task 3", "user_id": user_id, "status": "pending"}
    ]
    
    for task_data in tasks_data:
        test_db.add(Task(**task_data))
    await test_db.commit()

    pending_tasks = await repository.get_tasks_by_status(user_id, "pending")
    assert len(pending_tasks) == 2
    assert all(task.status == "pending" for task in pending_tasks)

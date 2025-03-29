import pytest
from fastapi.testclient import TestClient
from Backend.data_layer.database.models.task import Task, TaskStatus, TaskPriority
from Backend.services.task_service import TaskService, TaskUpdateError
from Backend.data_layer.repositories.task_repository import TaskRepository
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import json
from typing import Dict, List, Optional


@pytest.fixture
def client():
    from Backend.main import app
    return TestClient(app)


@pytest.fixture
def mock_task_repo():
    mock_repo = AsyncMock()

    # Setup default task
    default_task = Task(
        id=1,
        title="Test Task",
        description="Test Description",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.UPCOMING,
        creator_id=1,
        project_id=1,
        organization_id=1,
        _dependencies_list=json.dumps([]),
        progress_metrics={},
        blockers=[],
        actual_hours=10,
        estimated_hours=20,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Task with dependencies
    task_with_deps = Task(
        id=2,
        title="Task With Dependencies",
        description="This task has dependencies",
        priority=TaskPriority.HIGH,
        status=TaskStatus.UPCOMING,
        creator_id=1,
        project_id=1,
        organization_id=1,
        _dependencies_list=json.dumps([3, 4]),
        progress_metrics={},
        blockers=[],
        actual_hours=5,
        estimated_hours=15,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Dependency tasks
    dependency_task_1 = Task(
        id=3,
        title="Dependency Task 1",
        description="This is a dependency task",
        priority=TaskPriority.LOW,
        status=TaskStatus.COMPLETED,  # Already completed
        creator_id=1,
        project_id=1,
        organization_id=1,
        _dependencies_list=json.dumps([]),
        progress_metrics={},
        blockers=[],
        actual_hours=2,
        estimated_hours=5,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    dependency_task_2 = Task(
        id=4,
        title="Dependency Task 2",
        description="This is another dependency task",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.UPCOMING,  # Not completed yet
        creator_id=1,
        project_id=1,
        organization_id=1,
        _dependencies_list=json.dumps([]),
        progress_metrics={},
        blockers=[],
        actual_hours=0,
        estimated_hours=10,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Store tasks in a dictionary for easy access
    tasks = {
        1: default_task,
        2: task_with_deps,
        3: dependency_task_1,
        4: dependency_task_2
    }

    # Setup mock methods with Task object returns
    async def create_task_mock(**kwargs):
        task_id = max(tasks.keys()) + 1 if tasks else 1
        task = Task(
            id=task_id,
            title=kwargs.get('title', 'Test Task'),
            description=kwargs.get('description', 'Test Description'),
            status=kwargs.get('status', TaskStatus.UPCOMING),
            creator_id=kwargs.get('creator_id', 1),
            project_id=kwargs.get('project_id', 1),
            organization_id=kwargs.get('organization_id', 1),
            priority=kwargs.get('priority', TaskPriority.MEDIUM),
            _dependencies_list=kwargs.get(
                '_dependencies_list', json.dumps([])),
            progress_metrics={},
            blockers=[],
            actual_hours=0,
            estimated_hours=kwargs.get('estimated_hours', 0),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        # Ensure dependencies are properly set
        task.dependencies = kwargs.get('dependencies', [])
        task.task_dependencies = kwargs.get('dependencies', [])
        tasks[task_id] = task
        return task

    async def get_task_mock(task_id: int):
        task = tasks.get(task_id)
        if task:
            # Ensure dependencies are properly set
            task.dependencies = json.loads(task._dependencies_list)
            task.task_dependencies = json.loads(task._dependencies_list)
        return task

    async def update_task_mock(task_id: int, task_data: Dict):
        task = tasks.get(task_id)
        if not task:
            return None

        # Update task fields
        for key, value in task_data.items():
            if key != 'dependencies' and key != 'task_dependencies' and hasattr(task, key):
                setattr(task, key, value)

        # Handle dependencies
        if 'dependencies' in task_data:
            task.dependencies = task_data['dependencies']
            task.task_dependencies = task_data['dependencies']
            task._dependencies_list = json.dumps(task_data['dependencies'])

        task.updated_at = datetime.utcnow()
        return task

    async def delete_task_mock(task_id: int):
        if task_id in tasks:
            del tasks[task_id]
            return True
        return False

    async def get_task_metrics_mock(task_id: int):
        task = tasks.get(task_id)
        if not task:
            return None

        return {
            "time_spent": task.actual_hours,
            "estimated_completion": task.estimated_hours,
            "progress_percentage": (task.actual_hours / task.estimated_hours * 100) if task.estimated_hours else 0,
            "health_score": 0.85
        }

    # Assign the mock methods
    mock_repo.create_task = AsyncMock(side_effect=create_task_mock)
    mock_repo.get_task = AsyncMock(side_effect=get_task_mock)
    mock_repo.update_task = AsyncMock(side_effect=update_task_mock)
    mock_repo.delete_task = AsyncMock(side_effect=delete_task_mock)
    mock_repo.get_task_with_details = AsyncMock(side_effect=get_task_mock)
    mock_repo.add_task_history = AsyncMock()
    mock_repo.get_task_metrics = AsyncMock(side_effect=get_task_metrics_mock)

    return mock_repo


@pytest.fixture
def mock_rag_service():
    """Create a mock RAG service to avoid ChromaDB initialization."""
    mock_rag = MagicMock()

    async def mock_query_knowledge_base(*args, **kwargs):
        return {
            "answer": "Mocked RAG response",
            "sources": [],
            "confidence": 0.9
        }

    mock_rag.query_knowledge_base = AsyncMock(
        side_effect=mock_query_knowledge_base)
    mock_rag.add_to_knowledge_base = AsyncMock(return_value=True)
    mock_rag.update_document = AsyncMock(return_value=True)
    mock_rag.delete_document = AsyncMock(return_value=True)
    mock_rag.get_collection_stats = AsyncMock(
        return_value={"count": 10, "dimension": 384, "name": "test_collection"})

    return mock_rag


@pytest.fixture
def task_service(mock_task_repo, mock_rag_service):
    """Create a task service with mocked dependencies."""
    with patch('Backend.services.task_service.RAGService', return_value=mock_rag_service):
        service = TaskService(mock_task_repo)
        return service


@pytest.mark.asyncio
async def test_create_task(task_service):
    task = await task_service.create_task(
        title='New Test Task',
        description='New Test Description',
        creator_id=1,
        project_id=1,
        organization_id=1,
        dependencies=[1, 2]
    )
    assert task.title == 'New Test Task'
    assert task.description == 'New Test Description'
    assert json.loads(task._dependencies_list) == [1, 2]


@pytest.mark.asyncio
async def test_update_task(task_service):
    task = await task_service.update_task(
        task_id=1,
        task_data={
            'title': 'Updated Task',
            'description': 'Updated Description',
            'dependencies': [3, 4]
        }
    )
    assert task.title == 'Updated Task'
    assert task.description == 'Updated Description'
    assert json.loads(task._dependencies_list) == [3, 4]


@pytest.mark.asyncio
async def test_get_task(task_service):
    task = await task_service.get_task(1)
    assert task.title == 'Test Task'
    assert task.dependencies == []


@pytest.mark.asyncio
async def test_delete_task(task_service):
    result = await task_service.delete_task(1)
    assert result is True

    # Verify task is deleted
    task = await task_service.get_task(1)
    assert task is None


@pytest.mark.asyncio
async def test_update_task_status(task_service):
    # Update task status from TODO to IN_PROGRESS
    task = await task_service.update_task_status(
        task_id=1,
        new_status=TaskStatus.IN_PROGRESS,
        user_id=1
    )
    assert task.status == TaskStatus.IN_PROGRESS

    # Update to COMPLETED
    task = await task_service.update_task_status(
        task_id=1,
        new_status=TaskStatus.COMPLETED,
        user_id=1
    )
    assert task.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_check_dependencies(task_service):
    # Task 2 has dependencies on tasks 3 and 4
    # Task 3 is COMPLETED, but task 4 is not

    # This should return False since not all dependencies are completed
    result = await task_service.check_dependencies(2)
    assert result is False

    # Update task 4 to COMPLETED
    await task_service.update_task_status(
        task_id=4,
        new_status=TaskStatus.COMPLETED,
        user_id=1
    )

    # Now all dependencies are completed
    result = await task_service.check_dependencies(2)
    assert result is True


@pytest.mark.asyncio
async def test_get_task_metrics(task_service):
    metrics = await task_service.get_task_metrics(1)
    assert isinstance(metrics, dict)
    assert "time_spent" in metrics
    assert "estimated_completion" in metrics
    assert "progress_percentage" in metrics
    assert "health_score" in metrics

    assert metrics["time_spent"] == 10
    assert metrics["estimated_completion"] == 20


if __name__ == "__main__":
    import asyncio

    async def run_tests():
        # Setup
        mock_repo = mock_task_repo()
        mock_rag = mock_rag_service()

        with patch('Backend.services.task_service.RAGService', return_value=mock_rag):
            service = TaskService(mock_repo)

            # Run tests
            await test_create_task(service)
            await test_update_task(service)
            await test_get_task(service)
            await test_delete_task(service)
            await test_update_task_status(service)
            await test_check_dependencies(service)
            await test_get_task_metrics(service)

            print("All tests passed!")

    # Run the tests
    asyncio.run(run_tests())

import pytest
from fastapi.testclient import TestClient
from Backend.data_layer.database.models.task import Task, TaskStatus, TaskPriority
from Backend.services.task_service import TaskService, TaskUpdateError
from Backend.data_layer.repositories.task_repository import TaskRepository
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
import json
from typing import Dict


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

    # Setup mock methods with Task object returns
    async def create_task_mock(**kwargs):
        task = Task(
            id=1,
            title=kwargs.get('title', 'Test Task'),
            description=kwargs.get('description', 'Test Description'),
            status=kwargs.get('status', TaskStatus.UPCOMING),
            creator_id=kwargs.get('creator_id', 1),
            project_id=kwargs.get('project_id', 1),
            organization_id=kwargs.get('organization_id', 1),
            priority=kwargs.get('priority', TaskPriority.MEDIUM),
            _dependencies_list=json.dumps(kwargs.get('dependencies', [])),
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
        return task

    async def get_task_mock(task_id: int):
        task = default_task
        task.id = task_id
        # Ensure dependencies are properly set
        task.dependencies = json.loads(task._dependencies_list)
        task.task_dependencies = json.loads(task._dependencies_list)
        return task

    async def update_task_mock(task_id: int, updates: Dict):
        task = Task(
            id=task_id,
            title=updates.get('title', 'Test Task'),
            description=updates.get('description', 'Test Description'),
            status=updates.get('status', TaskStatus.UPCOMING),
            creator_id=1,
            project_id=1,
            organization_id=1,
            priority=updates.get('priority', TaskPriority.MEDIUM),
            category_id=updates.get('category_id'),
            parent_task_id=None,
            estimated_hours=20,
            due_date=updates.get('due_date'),
            _dependencies_list=json.dumps(updates.get('dependencies', [])),
            progress_metrics={"completed_steps": 5},
            actual_hours=10
        )
        # Ensure dependencies are properly set
        task.dependencies = updates.get('dependencies', [])
        task.task_dependencies = updates.get('dependencies', [])
        return task

    async def delete_task_mock(task_id: int):
        return True

    # Assign the mock methods
    mock_repo.create_task = AsyncMock(side_effect=create_task_mock)
    mock_repo.get_task = AsyncMock(side_effect=get_task_mock)
    mock_repo.update_task = AsyncMock(side_effect=update_task_mock)
    mock_repo.delete_task = AsyncMock(side_effect=delete_task_mock)
    mock_repo.get_task_with_details = AsyncMock(side_effect=get_task_mock)
    mock_repo.add_task_history = AsyncMock()

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
        title='Test Task',
        description='Test Description',
        creator_id=1,
        project_id=1,
        organization_id=1,
        dependencies=[1, 2]
    )
    assert task.title == 'Test Task'
    assert task.description == 'Test Description'
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

            print("All tests passed!")

    # Run the tests
    asyncio.run(run_tests())

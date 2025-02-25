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
    mock_repo = AsyncMock(spec=TaskRepository)

    # Setup default task
    default_task = Task(
        id=1,
        title="Test Task",
        description="Test Description",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.TODO,
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
            status=kwargs.get('status', TaskStatus.TODO),
            creator_id=kwargs.get('creator_id', 1),
            project_id=kwargs.get('project_id', 1),
            organization_id=kwargs.get('organization_id', 1),
            workflow_id=kwargs.get('workflow_id'),
            assignee_id=kwargs.get('assignee_id'),
            reviewer_id=kwargs.get('reviewer_id'),
            priority=kwargs.get('priority', TaskPriority.MEDIUM),
            category_id=kwargs.get('category_id'),
            parent_task_id=kwargs.get('parent_task_id'),
            estimated_hours=kwargs.get('estimated_hours'),
            due_date=kwargs.get('due_date'),
            _dependencies_list=json.dumps(kwargs.get('dependencies', []))
        )
        return task

    async def get_task_mock(task_id: int):
        task = Task(
            id=task_id,
            title='Test Task',
            description='Test Description',
            status=TaskStatus.TODO,
            creator_id=1,
            project_id=1,
            organization_id=1,
            workflow_id=None,
            assignee_id=None,
            reviewer_id=None,
            priority=TaskPriority.MEDIUM,
            category_id=None,
            parent_task_id=None,
            estimated_hours=20,
            due_date=None,
            _dependencies_list=json.dumps([1, 2]),
            progress_metrics={"completed_steps": 5},
            actual_hours=10,
            dependencies=[1, 2]
        )
        return task

    async def update_task_mock(task_id: int, updates: Dict):
        task = Task(
            id=task_id,
            title=updates.get('title', 'Test Task'),
            description=updates.get('description', 'Test Description'),
            status=updates.get('status', TaskStatus.TODO),
            creator_id=1,
            project_id=1,
            organization_id=1,
            workflow_id=None,
            assignee_id=updates.get('assignee_id'),
            reviewer_id=updates.get('reviewer_id'),
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
    mock_repo.create_task.side_effect = create_task_mock
    mock_repo.get_task.side_effect = get_task_mock
    mock_repo.update_task.side_effect = update_task_mock
    mock_repo.delete_task.side_effect = delete_task_mock
    mock_repo.get_task_with_details.side_effect = get_task_mock

    return mock_repo


@pytest.fixture
def task_service(mock_task_repo):
    return TaskService(mock_task_repo)


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
            'dependencies': [1, 2]
        }
    )
    assert task.title == 'Updated Task'
    assert task.description == 'Updated Description'
    assert json.loads(task._dependencies_list) == [1, 2]


@pytest.mark.asyncio
async def test_update_task_dependencies(task_service):
    task = await task_service.update_task(
        task_id=1,
        task_data={
            'dependencies': [2, 3]
        }
    )
    assert json.loads(task._dependencies_list) == [2, 3]

@pytest.mark.asyncio
async def test_update_task_status(task_service, mock_task_repo):
    task_id = 1
    user_id = 1
    new_status = TaskStatus.IN_PROGRESS

    # Mock task history creation
    mock_task_repo.add_task_history = AsyncMock()

    task = await task_service.update_task_status(task_id, new_status, user_id)
    assert task.status == new_status
    mock_task_repo.add_task_history.assert_called_once()

@pytest.mark.asyncio
async def test_invalid_status_transition(task_service):
    task_id = 1
    user_id = 1
    new_status = TaskStatus.COMPLETED  # Invalid transition from TODO to COMPLETED

    with pytest.raises(TaskUpdateError):
        await task_service.update_task_status(task_id, new_status, user_id)

@pytest.mark.asyncio
async def test_calculate_health_score(task_service):
    task = Task(
        id=1,
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        creator_id=1,
        project_id=1,
        organization_id=1
    )

    # Test blocked status impact
    score = await task_service._calculate_health_score(
        task,
        new_status=TaskStatus.BLOCKED,
        new_due_date=None,
        blockers={"reason": "dependency"}
    )
    assert score == 0.45  # 0.5 * 0.9 (blocked * blockers)

@pytest.mark.asyncio
async def test_detect_dependency_cycles(task_service, mock_task_repo):
    task_id = 1
    dependencies = [2, 3]

    # Mock tasks for cycle detection
    task1 = Task(id=1, dependencies=json.dumps([2]))
    task2 = Task(id=2, dependencies=json.dumps([3]))
    task3 = Task(id=3, dependencies=json.dumps([1]))

    mock_task_repo.get_task.side_effect = [task1, task2, task3]

    has_cycle = await task_service.detect_dependency_cycles(task_id, dependencies)
    assert has_cycle is True

@pytest.mark.asyncio
async def test_get_task_with_details(task_service, mock_task_repo):
    task_id = 1
    task = await task_service.get_task_with_details(task_id)

    assert task["id"] == 1
    assert "attachments" in task
    assert "comments" in task
    assert "history" in task


@pytest.mark.asyncio
async def test_get_task(task_service, mock_task_repo):
    task_id = 1
    result = await task_service.get_task(task_id)

    mock_task_repo.get_task.assert_called_once_with(task_id)
    assert result.title == "Test Task"
    assert isinstance(result.task_dependencies, list)


@pytest.mark.asyncio
async def test_delete_task(task_service, mock_task_repo):
    task_id = 1
    result = await task_service.delete_task(task_id)

    mock_task_repo.delete_task.assert_called_once_with(task_id)
    assert result is True


@pytest.mark.asyncio
async def test_update_task_dependencies(task_service):
    dependencies = [2, 3]
    task = await task_service.update_task(
        task_id=1,
        task_data={
            '_dependencies_list': json.dumps(dependencies)
        }
    )
    assert json.loads(task._dependencies_list) == dependencies


@pytest.mark.asyncio
async def test_check_task_dependencies(task_service, mock_task_repo):
    task_id = 1
    dependencies = [2, 3]

    # Create a task with dependencies
    task = Task(
        id=task_id,
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        creator_id=1,
        project_id=1,
        organization_id=1,
        _dependencies_list=json.dumps(dependencies),
        progress_metrics={},
        blockers=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Create completed dependent tasks
    dep_task = Task(
        id=2,
        title="Dependency Task",
        description="Dependency Description",
        status=TaskStatus.COMPLETED,
        priority=TaskPriority.MEDIUM,
        creator_id=1,
        project_id=1,
        organization_id=1,
        _dependencies_list=json.dumps([]),
        progress_metrics={},
        blockers=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Setup mock to return the task and its dependencies
    mock_task_repo.get_task.side_effect = [task, dep_task, dep_task]

    result = await task_service.check_dependencies(task_id)
    assert result is True


@pytest.mark.asyncio
async def test_get_task_metrics(task_service, mock_task_repo):
    task_id = 1

    # Create a task with metrics
    default_task = Task(
        id=1,
        title="Test Task",
        description="Test Description",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.TODO,
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
    
    mock_task_repo.get_task.return_value = default_task

    result = await task_service.get_task_metrics(task_id)
    assert result is not None
    assert "dependencies_completed" in result
    assert "time_spent" in result
    assert result["time_spent"] == 10
    assert result["estimated_completion"] == 20

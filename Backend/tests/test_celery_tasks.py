import pytest
from Backend.tasks.workflow_tasks import execute_workflow_step, process_workflow, StepStatus, WorkflowStatus
from Backend.tasks.ai_tasks import process_text_analysis, generate_productivity_insights
from Backend.tasks.notification_tasks import send_notification
from Backend.core.celery_app import (
    celery_app,
    create_todo_task,
    update_todo_task,
    delete_todo_task,
    get_todos,
    get_todo_by_id
)
import asyncio
from sqlalchemy import inspect
from datetime import datetime


@pytest.fixture(autouse=True)
def celery_test_setup():
    # Configure Celery for testing
    celery_app.conf.update(
        # Tasks are executed locally instead of being sent to queue
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,  # Exceptions are propagated
    )


@pytest.mark.asyncio
async def test_create_todo_task():
    todo_data = {
        "user_id": 1,
        "title": "Test Todo",
        "description": "Test Description",
        "priority": "medium",
        "due_date": datetime.utcnow().isoformat(),
        "is_recurring": False,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "dependencies": []  # Ensure dependencies are included
    }

    result = create_todo_task.delay(todo_data=todo_data)
    assert result.successful()
    data = result.get()

    assert data["title"] == todo_data["title"]
    assert data["description"] == todo_data["description"]
    assert data["user_id"] == todo_data["user_id"]


@pytest.mark.asyncio
async def test_update_todo_task():
    update_data = {
        "title": "Updated Todo",
        "description": "Updated Description",
        "status": "completed"
    }

    result = update_todo_task.delay(todo_id=1, user_id=1, updates=update_data)
    assert result.successful()
    data = result.get()

    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]
    assert data["status"] == update_data["status"]


@pytest.mark.asyncio
async def test_delete_todo_task():
    result = delete_todo_task.delay(todo_id=1, user_id=1)
    assert result.successful()
    success = result.get()
    assert success is True


@pytest.mark.asyncio
async def test_get_todos_task():
    result = get_todos.delay(user_id=1)
    assert result.successful()
    todos = result.get()
    assert isinstance(todos, list)


@pytest.mark.asyncio
async def test_get_todo_by_id_task():
    result = get_todo_by_id.delay(todo_id=1, user_id=1)
    assert result.successful()
    todo = result.get()
    assert todo is None or isinstance(todo, dict)


@pytest.mark.asyncio
async def test_execute_workflow_step():
    result = execute_workflow_step.delay(
        workflow_id=1,
        step_id=1,
        input_data={"test": "data"},
        user_id=1
    )
    assert result.successful()
    data = result.get()

    # Access dictionary values directly
    assert data.get("status") == StepStatus.SUCCESS
    assert data.get("workflow_id") == 1
    assert data.get("step_id") == 1
    assert "result" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_process_workflow():
    steps = [
        {
            "id": 1,
            "input": {"data": "test1"}
        },
        {
            "id": 2,
            "input": {"data": "test2"}
        }
    ]

    result = process_workflow.delay(
        workflow_id=1,
        steps=steps,
        user_id=1
    )
    assert result.successful()
    data = result.get()

    # Verify initial response structure using dictionary access
    assert data.get("workflow_id") == 1
    assert data.get("status") == WorkflowStatus.ACTIVE.value
    assert "task_id" in data
    assert len(data.get("steps", [])) == 2

    # Verify each step is pending using safe dictionary access
    for step in data.get("steps", []):
        assert "step_id" in step
        assert step.get("status") == StepStatus.PENDING


@pytest.mark.asyncio
async def test_process_text_analysis():
    result = process_text_analysis.delay(
        text="Sample text for analysis",
        analysis_type="sentiment",
        user_id=1,
        options={"detailed": True}
    )
    assert result.successful()
    data = result.get()

    # Use dictionary access for safer value checking
    assert data.get("status") == "success"
    assert "result" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_generate_productivity_insights():
    result = generate_productivity_insights.delay(
        user_id=1,
        time_period="daily",
        metrics=["focus", "efficiency"]
    )
    assert result.successful()
    data = result.get()

    # Safe dictionary access for nested data
    assert data.get("status") == "success"
    assert "insights" in data
    insights = data.get("insights", [])
    assert len(insights) == 2  # One for each metric


@pytest.mark.asyncio
async def test_send_notification():
    result = send_notification.delay(
        user_id=1,
        notification_type="workflow_complete",
        message="Workflow has completed successfully"
    )
    assert result.successful()
    data = result.get()

    # Use safe dictionary access for all values
    assert data.get("status") == "success"
    assert data.get("user_id") == 1
    assert "timestamp" in data

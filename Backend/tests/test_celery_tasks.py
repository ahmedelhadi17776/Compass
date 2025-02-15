import pytest
from Backend.tasks.workflow_tasks import execute_workflow_step, process_workflow, StepStatus
from Backend.tasks.ai_tasks import process_text_analysis, generate_productivity_insights
from Backend.tasks.notification_tasks import send_notification
from Backend.core.celery_app import celery_app
import asyncio


@pytest.fixture(autouse=True)
def celery_test_setup():
    # Configure Celery for testing
    celery_app.conf.update(
        # Tasks are executed locally instead of being sent to queue
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,  # Exceptions are propagated
    )


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
    assert data["status"] == StepStatus.SUCCESS
    assert data["workflow_id"] == 1
    assert data["step_id"] == 1
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
    assert data["workflow_id"] == 1
    assert len(data["steps"]) == 2
    assert all(step["status"] ==
               StepStatus.COMPLETED for step in data["steps"])


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
    assert data["status"] == "success"
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
    assert data["status"] == "success"
    assert "insights" in data
    assert len(data["insights"]) == 2  # One for each metric


@pytest.mark.asyncio
async def test_send_notification():
    result = send_notification.delay(
        user_id=1,
        notification_type="workflow_complete",
        message="Workflow has completed successfully"
    )
    assert result.successful()
    data = result.get()
    assert data["status"] == "success"
    assert data["user_id"] == 1
    assert "timestamp" in data

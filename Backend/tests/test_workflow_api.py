import pytest
from fastapi import status
from httpx import AsyncClient
import redis.asyncio as redis
from Backend.core.config import settings
from Backend.data_layer.database.models.workflow import WorkflowStatus
from Backend.tasks.workflow_tasks import StepStatus
from Backend.main import app
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
import datetime
from Backend.data_layer.database.models.user import User
from Backend.data_layer.database.models.workflow import Workflow
from Backend.data_layer.database.models.organization import Organization
import uuid
import json
from sqlalchemy import select


@pytest.fixture
async def test_user_and_org(db_session: AsyncSession) -> tuple[User, Organization]:
    """Create test user and organization."""
    try:
        # Create test organization first
        test_org = Organization(
            name="Test Organization",
            description="Test Description"
        )
        db_session.add(test_org)
        await db_session.flush()

        # Create test user with organization
        test_user = User(
            email="test@example.com",
            password_hash="test_password",
            is_active=True,
            username="test_user",
            organization_id=test_org.id  # Set organization_id directly
        )
        db_session.add(test_user)
        await db_session.flush()

        await db_session.commit()
        return test_user, test_org
    except Exception as e:
        await db_session.rollback()
        raise e


@pytest.mark.asyncio
async def test_create_workflow(client: AsyncClient, db_session: AsyncSession, test_user_and_org: tuple[User, Organization]):
    """Test creating a workflow."""
    test_user, test_org = test_user_and_org

    workflow_data = {
        "user_id": test_user.id,
        "organization_id": test_org.id,
        "name": "Test Workflow",
        "description": "Test workflow description",
        "steps": [
            {
                "id": 1,
                "name": "Step 1",
                "type": "test",
                "config": {},
                "input": {}
            }
        ]
    }

    # Create workflow
    response = await client.post("/workflows/", json=workflow_data)
    assert response.status_code == 201
    response_data = response.json()

    # Verify workflow was created
    workflow_id = response_data["workflow_id"]
    result = await db_session.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one()

    assert workflow is not None
    assert workflow.name == workflow_data["name"]
    assert workflow.created_by == test_user.id
    assert workflow.organization_id == test_org.id
    assert workflow.status == WorkflowStatus.PENDING.value


@pytest.mark.asyncio
async def test_execute_workflow_step(client: AsyncClient, db_session: AsyncSession, test_user_and_org: tuple[User, Organization]):
    """Test executing a workflow step."""
    test_user, test_org = test_user_and_org

    workflow_data = {
        "user_id": test_user.id,
        "organization_id": test_org.id,
        "name": "Test Workflow",
        "description": "Test workflow description",
        "steps": [
            {
                "id": 1,
                "name": "Step 1",
                "type": "test",
                "config": {},
                "input": {}
            }
        ]
    }

    # Create workflow
    create_response = await client.post("/workflows/", json=workflow_data)
    assert create_response.status_code == 201
    workflow_id = create_response.json()["workflow_id"]

    # Execute workflow step
    step_data = {
        "user_id": test_user.id,
        "input_data": {"test": "data"}
    }

    response = await client.post(f"/workflows/{workflow_id}/steps/1/execute", json=step_data)
    assert response.status_code == 200

    # Verify step execution
    result = await db_session.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one()

    assert workflow is not None
    assert workflow.status == WorkflowStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_analyze_workflow(client: AsyncClient, db_session: AsyncSession, test_user_and_org: tuple[User, Organization]):
    """Test analyzing a workflow."""
    test_user, test_org = test_user_and_org

    workflow_data = {
        "user_id": test_user.id,
        "organization_id": test_org.id,
        "name": "Test Workflow",
        "description": "Test workflow description",
        "steps": [
            {
                "id": 1,
                "name": "Step 1",
                "type": "test",
                "config": {},
                "input": {}
            }
        ]
    }

    # Create workflow
    create_response = await client.post("/workflows/", json=workflow_data)
    assert create_response.status_code == 201
    workflow_id = create_response.json()["workflow_id"]

    # Analyze workflow
    analysis_data = {
        "user_id": test_user.id,
        "analysis_type": "performance",
        "time_range": "1d",
        "metrics": ["duration", "success_rate"]
    }

    response = await client.post(f"/workflows/{workflow_id}/analyze", json=analysis_data)
    assert response.status_code == 200

    # Verify analysis results
    result = await db_session.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one()

    assert workflow is not None
    assert workflow.workflow_metadata is not None
    assert "analysis" in workflow.workflow_metadata


@pytest.mark.asyncio
async def test_cancel_workflow(client: AsyncClient, db_session: AsyncSession, test_user_and_org: tuple[User, Organization]):
    """Test canceling a workflow."""
    test_user, test_org = test_user_and_org

    workflow_data = {
        "user_id": test_user.id,
        "organization_id": test_org.id,
        "name": "Test Workflow",
        "description": "Test workflow description",
        "steps": [
            {
                "id": 1,
                "name": "Step 1",
                "type": "test",
                "config": {},
                "input": {}
            }
        ]
    }

    # Create workflow
    create_response = await client.post("/workflows/", json=workflow_data)
    assert create_response.status_code == 201
    workflow_id = create_response.json()["workflow_id"]

    # Cancel workflow
    cancel_data = {
        "user_id": test_user.id,
        "reason": "Test cancellation"
    }

    response = await client.post(f"/workflows/{workflow_id}/cancel", json=cancel_data)
    assert response.status_code == 200

    # Verify workflow was canceled
    result = await db_session.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one()

    assert workflow is not None
    assert workflow.status == WorkflowStatus.CANCELLED.value

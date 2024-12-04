from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from src.data.database.models.task import (
    Task, TaskComment, TaskHistory, TaskAttachment
)
from src.data.database.models.summary import SummarizedContent
from src.data.database.models.workflow import WorkflowStep, Workflow
from src.data.database.models import (
    TaskStatus, TaskPriority, TaskCategory,
    Tag
)

@pytest.mark.asyncio
async def test_create_task_with_relationships(async_session: AsyncSession, test_user):
    """Test creating a task with all its relationships."""
    # Create status and priority first
    status = TaskStatus(name="In Progress")
    priority = TaskPriority(name="High")
    async_session.add_all([status, priority])
    await async_session.commit()
    
    # Create tags
    tag1 = Tag(name="urgent")
    tag2 = Tag(name="review")
    async_session.add_all([tag1, tag2])
    await async_session.commit()
    
    # Create task
    task = Task(
        title="Test Task",
        description="Test task description",
        due_date=datetime.now(ZoneInfo("UTC")) + timedelta(days=1),
        user_id=test_user.id,
        status_id=status.id,
        priority_id=priority.id,
        created_at=datetime.now(ZoneInfo("UTC"))
    )
    
    # Add tags to task
    task.tags.extend([tag1, tag2])
    async_session.add(task)
    await async_session.commit()
    
    # Refresh task to get relationships
    stmt = select(Task).where(Task.id == task.id).options(
        selectinload(Task.tags),
        selectinload(Task.status),
        selectinload(Task.priority)
    )
    result = await async_session.execute(stmt)
    task = result.scalar_one()
    
    # Verify relationships
    assert task.status.name == "In Progress"
    assert task.priority.name == "High"
    assert len(task.tags) == 2
    assert {tag.name for tag in task.tags} == {"urgent", "review"}

@pytest.mark.asyncio
async def test_task_comments_and_history(async_session, test_user):
    """Test task comments and history tracking."""
    task = Task(
        title="Test Task",
        description="Test Description",
        status_id=1,
        priority_id=1,
        due_date=datetime.now(ZoneInfo("UTC")) + timedelta(days=1),
        user_id=test_user.id
    )
    async_session.add(task)
    await async_session.commit()

    # Add a comment
    comment = TaskComment(
        task_id=task.id,
        user_id=test_user.id,
        content="Test comment"
    )
    async_session.add(comment)

    # Add history entry
    history = TaskHistory(
        task_id=task.id,
        user_id=test_user.id,
        change_type="comment_added",
        old_value=None,
        new_value={"comment_id": 1, "content": "Test comment"}
    )
    async_session.add(history)
    await async_session.commit()

    # Refresh task with relationships
    stmt = select(Task).where(Task.id == task.id).options(
        selectinload(Task.comments),
        selectinload(Task.history)
    )
    result = await async_session.execute(stmt)
    task = result.scalar_one()
    
    assert len(task.comments) >= 1
    assert len(task.history) >= 1

@pytest.mark.asyncio
async def test_task_attachments(async_session, test_user):
    """Test task attachments."""
    task = Task(
        title="Test Task",
        description="Test Description",
        status_id=1,
        priority_id=1,
        due_date=datetime.now(ZoneInfo("UTC")) + timedelta(days=1),
        user_id=test_user.id
    )
    async_session.add(task)
    await async_session.commit()

    attachment = TaskAttachment(
        task_id=task.id,
        file_name="test.txt",
        file_path="/path/to/test.txt",
        file_type="text/plain",
        file_size=1024,
        uploaded_by=test_user.id
    )
    async_session.add(attachment)
    await async_session.commit()

    # Refresh task with relationships
    stmt = select(Task).where(Task.id == task.id).options(
        selectinload(Task.attachments)
    )
    result = await async_session.execute(stmt)
    task = result.scalar_one()

    assert len(task.attachments) >= 1

@pytest.mark.asyncio
async def test_task_summarization(async_session, test_user):
    """Test task summarization."""
    task = Task(
        title="Test Task",
        description="Test Description",
        status_id=1,
        priority_id=1,
        due_date=datetime.now(ZoneInfo("UTC")) + timedelta(days=1),
        user_id=test_user.id
    )
    async_session.add(task)
    await async_session.commit()

    summary = SummarizedContent(
        task_id=task.id,
        summary="Test summary",
        key_points='["point1", "point2"]'
    )
    async_session.add(summary)
    await async_session.commit()

    # Refresh task with relationships
    stmt = select(Task).where(Task.id == task.id).options(
        selectinload(Task.summary)
    )
    result = await async_session.execute(stmt)
    task = result.scalar_one()

    assert task.summary is not None
    assert task.summary.summary == "Test summary"

@pytest.mark.asyncio
async def test_workflow_steps(async_session, test_user):
    """Test workflow steps."""
    # Create workflow
    workflow = Workflow(
        name="Test Workflow",
        description="Test workflow description",
        created_by=test_user.id
    )
    async_session.add(workflow)
    await async_session.commit()

    # Create workflow steps
    steps = []
    for i in range(3):
        step = WorkflowStep(
            workflow_id=workflow.id,
            name=f"Step {i+1}",
            description=f"Description {i+1}",
            order=i+1
        )
        steps.append(step)
        async_session.add(step)
    await async_session.commit()

    # Create task with workflow
    task = Task(
        title="Test Task",
        description="Test Description",
        status_id=1,
        priority_id=1,
        due_date=datetime.now(ZoneInfo("UTC")) + timedelta(days=1),
        user_id=test_user.id,
        workflow_step_id=steps[0].id
    )
    async_session.add(task)
    await async_session.commit()

    # Link steps
    for i in range(len(steps)-1):
        # Load next_steps relationship
        stmt = select(WorkflowStep).where(WorkflowStep.id == steps[i].id).options(
            selectinload(WorkflowStep.next_steps)
        )
        result = await async_session.execute(stmt)
        step = result.scalar_one()
        step.next_steps.append(steps[i + 1])
    await async_session.commit()

    # Refresh task with relationships
    stmt = select(Task).where(Task.id == task.id).options(
        selectinload(Task.workflow_step)
    )
    result = await async_session.execute(stmt)
    task = result.scalar_one()

    assert task.workflow_step_id == steps[0].id

@pytest.mark.asyncio
async def test_task_constraints(async_session, test_user):
    """Test task constraints."""
    # Test due date after creation constraint
    with pytest.raises(IntegrityError):
        task = Task(
            title="Invalid Task",
            description="Task with invalid dates",
            status_id=1,
            priority_id=1,
            due_date=datetime.now(ZoneInfo("UTC")) - timedelta(days=1),  # Due date before creation
            user_id=test_user.id
        )
        async_session.add(task)
        await async_session.commit()

@pytest.mark.asyncio
async def test_task_status_transitions(async_session, test_user):
    """Test task status transitions."""
    # Create task statuses
    statuses = []
    for i, name in enumerate(['New', 'In Progress', 'Done']):
        status = TaskStatus(
            name=name,
            description=f"Description for {name}",
            color_code=f"#{'1'*6}"
        )
        statuses.append(status)
        async_session.add(status)
    await async_session.commit()

    # Create task with initial status
    task = Task(
        title="Test Task",
        description="Test Description",
        status_id=statuses[0].id,
        priority_id=1,
        due_date=datetime.now(ZoneInfo("UTC")) + timedelta(days=1),
        user_id=test_user.id
    )
    async_session.add(task)
    await async_session.commit()

    # Transition through statuses
    for status in statuses[1:]:
        task.status_id = status.id
        # Add history entry for status change
        history = TaskHistory(
            task_id=task.id,
            user_id=test_user.id,
            change_type="status_changed",
            old_value={"status_id": status.id - 1},
            new_value={"status_id": status.id}
        )
        async_session.add(history)
        await async_session.commit()

    # Verify final status and history
    stmt = select(Task).where(Task.id == task.id).options(
        selectinload(Task.status),
        selectinload(Task.history)
    )
    result = await async_session.execute(stmt)
    task = result.scalar_one()

    assert task.status.name == "Done"
    assert len(task.history) >= 2  # At least 2 status changes

@pytest.mark.asyncio
async def test_task_priority_changes(async_session, test_user):
    """Test task priority changes."""
    # Create task priorities
    priorities = []
    for i, (name, weight) in enumerate([('Low', 1), ('Medium', 2), ('High', 3)]):
        priority = TaskPriority(
            name=name,
            description=f"Description for {name}",
            weight=weight,
            color_code=f"#{'1'*6}"
        )
        priorities.append(priority)
        async_session.add(priority)
    await async_session.commit()

    # Create task with initial priority
    task = Task(
        title="Test Task",
        description="Test Description",
        status_id=1,
        priority_id=priorities[0].id,
        due_date=datetime.now(ZoneInfo("UTC")) + timedelta(days=1),
        user_id=test_user.id
    )
    async_session.add(task)
    await async_session.commit()

    # Change priority
    task.priority_id = priorities[2].id  # Change to High priority
    history = TaskHistory(
        task_id=task.id,
        user_id=test_user.id,
        change_type="priority_changed",
        old_value={"priority_id": priorities[0].id},
        new_value={"priority_id": priorities[2].id}
    )
    async_session.add(history)
    await async_session.commit()

    # Verify priority change and history
    stmt = select(Task).where(Task.id == task.id).options(
        selectinload(Task.priority),
        selectinload(Task.history)
    )
    result = await async_session.execute(stmt)
    task = result.scalar_one()

    assert task.priority.name == "High"
    assert task.priority.weight == 3
    assert len(task.history) >= 1

@pytest.mark.asyncio
async def test_task_category_assignments(async_session, test_user):
    """Test task category assignments."""
    # Create task categories
    parent_category = TaskCategory(
        name="Work",
        description="Work related tasks",
        color_code="#111111"
    )
    async_session.add(parent_category)
    await async_session.commit()

    child_category = TaskCategory(
        name="Project",
        description="Project specific tasks",
        color_code="#222222",
        parent_id=parent_category.id
    )
    async_session.add(child_category)
    await async_session.commit()

    # Create task with category
    task = Task(
        title="Test Task",
        description="Test Description",
        status_id=1,
        priority_id=1,
        category_id=child_category.id,
        due_date=datetime.now(ZoneInfo("UTC")) + timedelta(days=1),
        user_id=test_user.id
    )
    async_session.add(task)
    await async_session.commit()

    # Change category
    task.category_id = parent_category.id
    history = TaskHistory(
        task_id=task.id,
        user_id=test_user.id,
        change_type="category_changed",
        old_value={"category_id": child_category.id},
        new_value={"category_id": parent_category.id}
    )
    async_session.add(history)
    await async_session.commit()

    # Verify category change and history
    stmt = select(Task).where(Task.id == task.id).options(
        selectinload(Task.category),
        selectinload(Task.history)
    )
    result = await async_session.execute(stmt)
    task = result.scalar_one()

    assert task.category.name == "Work"
    assert len(task.history) >= 1

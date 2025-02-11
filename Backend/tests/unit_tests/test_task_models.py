from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pytest
from sqlalchemy import select, text, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from Backend.data.database.models.task import (
    Task, TaskComment, TaskHistory, TaskAttachment
)
from Backend.data.database.models.summary import Summary
from Backend.data.database.models.workflow import WorkflowStep, Workflow, WorkflowStepTransition
from Backend.data.database.models import (
    TaskStatus, TaskPriority, TaskCategory,
    Tag, User
)

@pytest.mark.asyncio
async def test_create_task_with_relationships(async_session: AsyncSession, test_user):
    """Test creating a task with all relationships."""
    # Create workflow
    workflow = Workflow(
        name="Test Workflow",
        description="Test workflow description",
        is_active=True,
        creator_id=test_user.id
    )
    async_session.add(workflow)
    await async_session.commit()

    # Create status
    status = TaskStatus(
        name="To Do",
        description="Tasks that need to be started",
        color="#808080"  # Gray
    )
    async_session.add(status)
    await async_session.commit()

    # Create category
    category = TaskCategory(
        name="Work",
        description="Work-related tasks",
        color="#0000FF"  # Blue
    )
    async_session.add(category)
    await async_session.commit()

    # Create tags
    tag1 = Tag(name="urgent")
    tag2 = Tag(name="feature")
    async_session.add_all([tag1, tag2])
    await async_session.commit()

    # Create task with all relationships
    task = Task(
        title="Test Task",
        description="Test task with all relationships",
        user_id=test_user.id,
        assignee_id=test_user.id,
        status_id=status.id,
        category_id=category.id,
        workflow_id=workflow.id,
        priority=TaskPriority.HIGH,
        due_date=datetime.now(ZoneInfo("UTC")) + timedelta(days=1),
        tags=[tag1, tag2]  # Add tags directly during task creation
    )
    async_session.add(task)
    await async_session.commit()

    # Add comment
    comment = TaskComment(
        task_id=task.id,
        user_id=test_user.id,
        content="Test comment"
    )
    async_session.add(comment)
    await async_session.commit()

    # Add attachment
    attachment = TaskAttachment(
        task_id=task.id,
        user_id=test_user.id,
        filename="test.txt",
        file_path="/path/to/test.txt",
        file_size=1024,
        mime_type="text/plain"
    )
    async_session.add(attachment)
    await async_session.commit()

    # Verify relationships
    stmt = select(Task).where(Task.id == task.id).options(
        selectinload(Task.user),
        selectinload(Task.assignee),
        selectinload(Task.status),
        selectinload(Task.category),
        selectinload(Task.workflow),
        selectinload(Task.comments),
        selectinload(Task.attachments),
        selectinload(Task.tags)
    )
    result = await async_session.execute(stmt)
    task = result.scalar_one()

    assert task.user_id == test_user.id
    assert task.assignee_id == test_user.id
    assert task.status.name == "To Do"
    assert task.category.name == "Work"
    assert task.workflow.name == "Test Workflow"
    assert len(task.comments) == 1
    assert task.comments[0].content == "Test comment"
    assert len(task.attachments) == 1
    assert task.attachments[0].filename == "test.txt"
    assert len(task.tags) == 2
    assert {tag.name for tag in task.tags} == {"urgent", "feature"}

@pytest.mark.asyncio
async def test_task_comments_and_history(async_session: AsyncSession):
    """Test task comments and history tracking."""
    # Create test user
    test_user = User(
        username="testuser_comments",
        email="testuser_comments@example.com",
        full_name="Test User Comments",
        hashed_password="dummyhash",
        is_active=True
    )
    async_session.add(test_user)

    # Create test status
    test_status = TaskStatus(
        name="Test Status",
        description="Test status description",
        color="#000000"
    )
    async_session.add(test_status)
    await async_session.flush()

    # Create task
    task = Task(
        title="Test Task",
        description="Test description",
        user_id=test_user.id,
        status_id=test_status.id,
        priority=TaskPriority.MEDIUM
    )
    async_session.add(task)
    await async_session.flush()

    # Add comment to task
    comment = TaskComment(
        task_id=task.id,
        user_id=test_user.id,
        content="Test comment"
    )
    async_session.add(comment)
    await async_session.flush()

    # Verify comment was added
    stmt = select(TaskComment).where(TaskComment.task_id == task.id)
    result = await async_session.execute(stmt)
    saved_comment = result.scalar_one()
    assert saved_comment.content == "Test comment"
    assert saved_comment.user_id == test_user.id

    # Update task description and track in history
    old_description = task.description
    task.description = "Updated description"
    await async_session.flush()

    # Record change in history
    history_entry = TaskHistory(
        task_id=task.id,
        user_id=test_user.id,
        action="update",
        field="description",
        old_value=old_description,
        new_value=task.description
    )
    async_session.add(history_entry)
    await async_session.flush()

    # Verify history entry was created
    stmt = select(TaskHistory).where(
        TaskHistory.task_id == task.id,
        TaskHistory.field == "description"
    )
    result = await async_session.execute(stmt)
    history = result.scalar_one()
    assert history is not None
    assert history.old_value == "Test description"
    assert history.new_value == "Updated description"

    # Test invalid comment (non-existent task)
    try:
        invalid_comment = TaskComment(
            task_id=999999,  # Non-existent task ID
            user_id=test_user.id,
            content="Invalid comment"
        )
        async_session.add(invalid_comment)
        await async_session.flush()
        pytest.fail("Should have raised IntegrityError")
    except IntegrityError:
        await async_session.rollback()

    # Test invalid history (non-existent task)
    try:
        invalid_history = TaskHistory(
            task_id=999999,  # Non-existent task ID
            user_id=test_user.id,
            action="update",
            field="status",
            old_value="old",
            new_value="new"
        )
        async_session.add(invalid_history)
        await async_session.flush()
        pytest.fail("Should have raised IntegrityError")
    except IntegrityError:
        await async_session.rollback()

@pytest.mark.asyncio
async def test_task_attachments(async_session: AsyncSession):
    """Test task attachments."""
    # Create test user
    test_user = User(
        username="testuser_attachments",
        email="testuser_attachments@example.com",
        full_name="Test User Attachments",
        hashed_password="dummyhash",
        is_active=True
    )
    async_session.add(test_user)
    await async_session.commit()

    # Create test status
    test_status = TaskStatus(
        name="Test Status",
        description="Test status description",
        color="#000000"
    )
    async_session.add(test_status)
    await async_session.commit()

    # Create task
    task = Task(
        title="Test Task",
        description="Test description",
        user_id=test_user.id,
        status_id=test_status.id,
        priority=TaskPriority.MEDIUM
    )
    async_session.add(task)
    await async_session.commit()

    # Add attachment
    attachment = TaskAttachment(
        task_id=task.id,
        user_id=test_user.id,
        filename="test.txt",
        file_path="/path/to/test.txt",
        file_size=1024,
        mime_type="text/plain"
    )
    async_session.add(attachment)
    await async_session.commit()

    # Verify attachment was added
    task_attachments = await async_session.execute(
        select(TaskAttachment).where(TaskAttachment.task_id == task.id)
    )
    attachment = task_attachments.scalar_one()
    assert attachment is not None
    assert attachment.filename == "test.txt"
    assert attachment.file_size == 1024
    assert attachment.mime_type == "text/plain"

    # Test invalid attachment (non-existent task)
    invalid_attachment = TaskAttachment(
        task_id=999999,  # Non-existent task ID
        user_id=test_user.id,
        filename="invalid.txt",
        file_path="/path/to/invalid.txt",
        file_size=2048,
        mime_type="text/plain"
    )
    async_session.add(invalid_attachment)
    with pytest.raises(IntegrityError) as exc_info:
        await async_session.commit()
    assert "FOREIGN KEY constraint failed" in str(exc_info.value)
    await async_session.rollback()

@pytest.mark.asyncio
async def test_task_summarization(async_session: AsyncSession):
    """Test task summarization."""
    # Create test user
    test_user = User(
        username="testuser_summary",
        email="testuser_summary@example.com",
        full_name="Test User Summary",
        hashed_password="dummyhash",
        is_active=True
    )
    async_session.add(test_user)
    await async_session.commit()

    # Create test status
    test_status = TaskStatus(
        name="Test Status",
        description="Test status description",
        color="#000000"
    )
    async_session.add(test_status)
    await async_session.commit()

    # Create task with comments
    task = Task(
        title="Test Task",
        description="Test description",
        user_id=test_user.id,
        status_id=test_status.id,
        priority=TaskPriority.MEDIUM
    )
    async_session.add(task)
    await async_session.commit()

    # Add comments
    comments = [
        TaskComment(
            task_id=task.id,
            user_id=test_user.id,
            content=f"Comment {i}"
        )
        for i in range(3)
    ]
    async_session.add_all(comments)
    await async_session.commit()

    # Verify comments were added
    task_comments = await async_session.execute(
        select(TaskComment)
        .where(TaskComment.task_id == task.id)
        .order_by(TaskComment.created_at)
    )
    comments = task_comments.scalars().all()
    assert len(comments) == 3
    for i, comment in enumerate(comments):
        assert comment.content == f"Comment {i}"

    # Add history entries
    history_entries = [
        TaskHistory(
            task_id=task.id,
            user_id=test_user.id,
            action="update",
            field=f"field_{i}",
            old_value="old",
            new_value="new"
        )
        for i in range(2)
    ]
    async_session.add_all(history_entries)
    await async_session.commit()

    # Verify history entries were added
    task_history = await async_session.execute(
        select(TaskHistory)
        .where(TaskHistory.task_id == task.id)
        .order_by(TaskHistory.created_at)
    )
    history = task_history.scalars().all()
    assert len(history) == 2
    for i, entry in enumerate(history):
        assert entry.field == f"field_{i}"
        assert entry.old_value == "old"
        assert entry.new_value == "new"

@pytest.mark.asyncio
async def test_workflow_steps(async_session: AsyncSession):
    """Test workflow steps."""
    # Create test user
    test_user = User(
        username="testuser_workflow",
        email="testuser_workflow@example.com",
        full_name="Test User Workflow",
        hashed_password="dummyhash",
        is_active=True
    )
    async_session.add(test_user)
    await async_session.commit()

    # Create test status
    test_status = TaskStatus(
        name="Test Status",
        description="Test status description",
        color="#000000"
    )
    async_session.add(test_status)
    await async_session.commit()

    # Create workflow
    workflow = Workflow(
        name="Test Workflow",
        description="Test workflow description",
        creator_id=test_user.id,
        is_active=True
    )
    async_session.add(workflow)
    await async_session.commit()

    # Create workflow steps
    steps = [
        WorkflowStep(
            workflow_id=workflow.id,
            name=f"Step {i}",
            description=f"Step {i} description",
            step_order=i,
            is_required=True,
            is_automated=False
        )
        for i in range(3)
    ]
    async_session.add_all(steps)
    await async_session.commit()

    # Create task with workflow
    task = Task(
        title="Test Task",
        description="Test description",
        user_id=test_user.id,
        status_id=test_status.id,
        workflow_id=workflow.id,
        priority=TaskPriority.MEDIUM
    )
    async_session.add(task)
    await async_session.commit()

    # Verify workflow steps
    result = await async_session.execute(
        select(WorkflowStep)
        .where(WorkflowStep.workflow_id == workflow.id)
        .order_by(WorkflowStep.step_order)
    )
    steps = result.scalars().all()
    assert len(steps) == 3
    for i, step in enumerate(steps):
        assert step.name == f"Step {i}"
        assert step.step_order == i

    # Test invalid workflow step (non-existent workflow)
    invalid_step = WorkflowStep(
        workflow_id=999999,  # Non-existent workflow ID
        name="Invalid Step",
        description="Invalid step description",
        step_order=0,
        is_required=True,
        is_automated=False
    )
    async_session.add(invalid_step)
    with pytest.raises(IntegrityError) as exc_info:
        await async_session.commit()
    assert "FOREIGN KEY constraint failed" in str(exc_info.value)
    await async_session.rollback()

@pytest.mark.asyncio
async def test_task_model_validation(async_session: AsyncSession):
    """Test task model validation."""
    # Create test user
    test_user = User(
        username="testuser_validation",
        email="testuser_validation@example.com",
        full_name="Test User Validation",
        hashed_password="dummyhash",
        is_active=True
    )
    async_session.add(test_user)
    await async_session.flush()
    await async_session.refresh(test_user)

    # Create test status
    test_status = TaskStatus(
        name="Test Status",
        description="Test status description",
        color="#000000"
    )
    async_session.add(test_status)
    await async_session.flush()
    await async_session.refresh(test_status)

    # Test valid task
    valid_task = Task(
        title="Test Task",
        description="Test description",
        user_id=test_user.id,
        status_id=test_status.id,
        priority=TaskPriority.MEDIUM
    )
    async_session.add(valid_task)
    await async_session.flush()
    await async_session.refresh(valid_task)

    # Test task without title (should fail)
    with pytest.raises(TypeError) as exc_info:
        Task(
            description="Test description",
            user_id=test_user.id,
            status_id=test_status.id,
            priority=TaskPriority.MEDIUM
        )
    assert "Title is required" in str(exc_info.value)

    # Test task with invalid priority (should fail)
    with pytest.raises(ValueError) as exc_info:
        Task(
            title="Test Task",
            description="Test description",
            user_id=test_user.id,
            status_id=test_status.id,
            priority="INVALID_PRIORITY"
        )
    assert "Invalid priority value" in str(exc_info.value)

    # Test task with non-existent user (should fail)
    invalid_task = Task(
        title="Test Task",
        description="Test description",
        user_id=999999,  # Non-existent user ID
        status_id=test_status.id,
        priority=TaskPriority.MEDIUM
    )
    async_session.add(invalid_task)
    with pytest.raises(IntegrityError) as exc_info:
        await async_session.flush()
    assert "FOREIGN KEY constraint failed" in str(exc_info.value)
    await async_session.rollback()

    await async_session.commit()

@pytest.mark.asyncio
async def test_task_database_constraints(async_session: AsyncSession):
    """Test task database constraints."""
    # Create test user
    test_user = User(
        username="testuser_constraints",
        email="testuser_constraints@example.com",
        full_name="Test User Constraints",
        hashed_password="dummyhash",
        is_active=True
    )
    async_session.add(test_user)
    await async_session.commit()  # Commit to persist the user

    # Create test status
    test_status = TaskStatus(
        name="Test Status",
        description="Test status description",
        color="#000000"
    )
    async_session.add(test_status)
    await async_session.commit()  # Commit to persist the status

    # Create task with initial title
    task1 = Task(
        title="Same Title",
        description="Task 1 description",
        user_id=test_user.id,
        status_id=test_status.id,
        priority=TaskPriority.MEDIUM
    )
    async_session.add(task1)
    await async_session.commit()  # Commit to persist task1

    # Try to create another task with the same title for the same user
    task2 = Task(
        title="Same Title",  # Same title as task1
        description="Task 2 description",
        user_id=test_user.id,
        status_id=test_status.id,
        priority=TaskPriority.HIGH
    )
    async_session.add(task2)

    try:
        await async_session.commit()  # Try to commit task2
        pytest.fail("Should have raised IntegrityError")
    except IntegrityError as e:
        assert "UNIQUE constraint failed" in str(e)
        await async_session.rollback()

    # Test cascading delete
    await async_session.delete(test_user)
    await async_session.commit()  # Commit the deletion

    # Verify task was deleted
    stmt = select(Task).where(Task.user_id == test_user.id)
    result = await async_session.execute(stmt)
    deleted_task = result.scalar_one_or_none()
    assert deleted_task is None

@pytest.mark.asyncio
async def test_task_status_transitions(async_session: AsyncSession):
    """Test task status transitions."""
    # Create test user
    test_user = User(
        username="testuser_status",
        email="testuser_status@example.com",
        full_name="Test User Status",
        hashed_password="dummyhash",
        is_active=True
    )
    async_session.add(test_user)
    await async_session.commit()

    # Create test statuses with transitions
    todo_status = TaskStatus(
        name="Todo",
        description="Todo status",
        color="#000000"
    )
    in_progress_status = TaskStatus(
        name="In Progress",
        description="In progress status",
        color="#FFFFFF"
    )
    done_status = TaskStatus(
        name="Done",
        description="Done status",
        color="#00FF00"
    )
    async_session.add_all([todo_status, in_progress_status, done_status])
    await async_session.commit()

    # Create task with initial status
    task = Task(
        title="Test Task",
        description="Test description",
        user_id=test_user.id,
        status_id=todo_status.id,
        priority=TaskPriority.MEDIUM
    )
    async_session.add(task)
    await async_session.commit()

    # Test valid status transition
    task.status_id = in_progress_status.id
    await async_session.commit()

    # Verify status was updated
    result = await async_session.execute(
        select(Task).where(Task.id == task.id)
    )
    updated_task = result.scalar_one()
    assert updated_task.status_id == in_progress_status.id

    # Record status change in history
    history_entry = TaskHistory(
        task_id=task.id,
        user_id=test_user.id,
        action="update",
        field="status",
        old_value=str(todo_status.id),
        new_value=str(in_progress_status.id)
    )
    async_session.add(history_entry)
    await async_session.commit()

    # Verify history entry was created
    result = await async_session.execute(
        select(TaskHistory)
        .where(TaskHistory.task_id == task.id)
        .where(TaskHistory.field == "status")
    )
    history = result.scalar_one()
    assert history is not None
    assert history.old_value == str(todo_status.id)
    assert history.new_value == str(in_progress_status.id)

@pytest.mark.asyncio
async def test_task_priority_changes(async_session: AsyncSession):
    """Test task priority changes."""
    # Create test user
    test_user = User(
        username="testuser_priority",
        email="testuser_priority@example.com",
        full_name="Test User Priority",
        hashed_password="dummyhash",
        is_active=True
    )
    async_session.add(test_user)

    # Create test status
    test_status = TaskStatus(
        name="Test Status",
        description="Test status description",
        color="#000000"
    )
    async_session.add(test_status)
    await async_session.flush()

    # Create task with initial priority
    task = Task(
        title="Test Task",
        description="Test description",
        user_id=test_user.id,
        status_id=test_status.id,
        priority=TaskPriority.LOW
    )
    async_session.add(task)
    await async_session.flush()

    # Test changing priority
    old_priority = task.priority
    task.priority = TaskPriority.HIGH
    await async_session.flush()

    # Verify priority was updated
    stmt = select(Task).where(Task.id == task.id)
    result = await async_session.execute(stmt)
    updated_task = result.scalar_one()
    assert updated_task.priority == TaskPriority.HIGH

    # Record priority change in history
    history_entry = TaskHistory(
        task_id=task.id,
        user_id=test_user.id,
        action="update",
        field="priority",
        old_value=old_priority.value,
        new_value=TaskPriority.HIGH.value
    )
    async_session.add(history_entry)
    await async_session.flush()

    # Verify history entry was created
    stmt = select(TaskHistory).where(
        TaskHistory.task_id == task.id,
        TaskHistory.field == "priority"
    )
    result = await async_session.execute(stmt)
    history = result.scalar_one()
    assert history is not None
    assert history.old_value == TaskPriority.LOW.value
    assert history.new_value == TaskPriority.HIGH.value

    # Test setting invalid priority value
    try:
        task.priority = "INVALID_PRIORITY"  # This should raise ValueError
        await async_session.flush()
        pytest.fail("Should have raised ValueError")
    except ValueError:
        await async_session.rollback()

@pytest.mark.asyncio
async def test_task_category_assignments(async_session: AsyncSession):
    """Test task category assignments."""
    # Create test user
    test_user = User(
        username="testuser_category",
        email="testuser_category@example.com",
        full_name="Test User Category",
        hashed_password="dummyhash",
        is_active=True
    )
    async_session.add(test_user)
    await async_session.commit()

    # Create test status
    test_status = TaskStatus(
        name="Test Status",
        description="Test status description",
        color="#000000"
    )
    async_session.add(test_status)
    await async_session.commit()

    # Create test categories
    category1 = TaskCategory(
        name="Category 1",
        description="Category 1 description",
        color="#FF0000"
    )
    category2 = TaskCategory(
        name="Category 2",
        description="Category 2 description",
        color="#00FF00"
    )
    async_session.add_all([category1, category2])
    await async_session.commit()

    # Create task with initial category
    task = Task(
        title="Test Task",
        description="Test description",
        user_id=test_user.id,
        status_id=test_status.id,
        priority=TaskPriority.MEDIUM,
        category_id=category1.id
    )
    async_session.add(task)
    await async_session.commit()

    # Verify initial category assignment
    result = await async_session.execute(
        select(Task).where(Task.id == task.id)
    )
    task = result.scalar_one()
    assert task.category_id == category1.id

    # Change category
    old_category_id = task.category_id
    task.category_id = category2.id
    await async_session.commit()

    # Verify category was updated
    result = await async_session.execute(
        select(Task).where(Task.id == task.id)
    )
    updated_task = result.scalar_one()
    assert updated_task.category_id == category2.id

    # Record category change in history
    history_entry = TaskHistory(
        task_id=task.id,
        user_id=test_user.id,
        action="update",
        field="category",
        old_value=str(old_category_id),
        new_value=str(category2.id)
    )
    async_session.add(history_entry)
    await async_session.commit()

    # Verify history entry was created
    result = await async_session.execute(
        select(TaskHistory)
        .where(TaskHistory.task_id == task.id)
        .where(TaskHistory.field == "category")
    )
    history = result.scalar_one()
    assert history is not None
    assert history.old_value == str(category1.id)
    assert history.new_value == str(category2.id)

    # Test invalid category ID
    task.category_id = 999999  # Non-existent category ID
    with pytest.raises(IntegrityError) as exc_info:
        await async_session.commit()
    assert "FOREIGN KEY constraint failed" in str(exc_info.value)
    await async_session.rollback()

    # Test removing category (setting to None)
    task.category_id = None
    await async_session.commit()

    # Verify category was removed
    result = await async_session.execute(
        select(Task).where(Task.id == task.id)
    )
    updated_task = result.scalar_one()
    assert updated_task.category_id is None

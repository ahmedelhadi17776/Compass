from celery import Celery, shared_task
from celery.signals import worker_init
from Backend.core.config import settings
from Backend.data_layer.database.connection import get_db
from Backend.data_layer.database.models.task import Task
from Backend.data_layer.database.session import get_db_session
import asyncio

# Create Celery instance
celery_app = Celery(
    "compass",
    backend=settings.CELERY_RESULT_BACKEND,
    broker=settings.CELERY_BROKER_URL,
    include=[
        "tasks.email_tasks",
        "tasks.workflow_tasks",
        "tasks.ai_tasks",
        "tasks.notification_tasks"
    ]
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_store_errors_even_if_ignored=True,
    task_send_sent_event=True,
    task_ignore_result=False,
    result_expires=3600,  # Results expire in 1 hour
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    task_routes={
        "tasks.email_tasks.*": {"queue": "email"},
        "tasks.workflow_tasks.*": {"queue": "workflow"},
        "tasks.ai_tasks.*": {"queue": "ai"},
        "tasks.notification_tasks.*": {"queue": "notification"}
    },
    task_default_priority=5,
    task_max_priority=10,
    task_create_missing_queues=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_store_eager_result=True,  # Store results even in eager mode
    task_eager_propagates=True,  # Propagate exceptions in eager mode
    # Use settings value for eager mode
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    result_backend_always_retry=True,  # Always retry backend operations
    result_backend_max_retries=10,  # Maximum number of retries for backend operations
    redis_backend_use_ssl=False,  # Disable SSL for Redis in test mode
    redis_max_connections=None,  # No connection limit in test mode
    broker_connection_retry=True,  # Retry broker connections
    broker_connection_max_retries=None,  # Unlimited retries for broker connections
    beat_schedule={
        'check-task-dependencies': {
            'task': 'tasks.task_tasks.check_dependencies',
            'schedule': 300.0,  # Every 5 minutes
            'args': None
        }
    }
)

# Configure task routing
celery_app.conf.task_routes = {
    "tasks.email_tasks.*": {"queue": "email"},
    "tasks.workflow_tasks.*": {"queue": "workflow"},
    "tasks.ai_tasks.*": {"queue": "ai"},
    "tasks.notification_tasks.*": {"queue": "notification"}
}

# Configure task priorities
celery_app.conf.task_queue_max_priority = 10
celery_app.conf.task_default_priority = 5

# Configure task rate limits
celery_app.conf.task_annotations = {
    "tasks.email_tasks.send_email": {"rate_limit": "100/m"},
    "tasks.ai_tasks.*": {"rate_limit": "50/m"}
}


def run_async(coro):
    created_loop = False
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        created_loop = True
    try:
        return loop.run_until_complete(coro)
    finally:
        if created_loop:
            loop.close()


@shared_task
def create_todo_task(todo_data: dict):
    async def _create():
        async with get_db_session() as session:
            todo = Task(**todo_data)
            session.add(todo)
            await session.commit()
            await session.refresh(todo)
            return todo
    return run_async(_create())


@shared_task
def update_todo_task(todo_id, user_id, updates):
    from Backend.data_layer.repositories.todo_repository import TodoRepository

    async def _update():
        async for db in get_db():
            todo_repo = TodoRepository()
            return await todo_repo.update(todo_id, user_id, **updates)
    return run_async(_update())


@shared_task
def delete_todo_task(todo_id, user_id):
    from Backend.data_layer.repositories.todo_repository import TodoRepository

    async def _delete():
        async for db in get_db():
            todo_repo = TodoRepository()
            return await todo_repo.delete(todo_id, user_id)
    return run_async(_delete())


@shared_task
def get_todos(user_id):
    from Backend.data_layer.repositories.todo_repository import TodoRepository

    async def _get_todos():
        async for db in get_db():
            todo_repo = TodoRepository()
            return await todo_repo.get_user_todos(user_id)
    return run_async(_get_todos())


@shared_task
def get_todo_by_id(todo_id, user_id):
    from Backend.data_layer.repositories.todo_repository import TodoRepository

    async def _get_by_id():
        async for db in get_db():
            todo_repo = TodoRepository()
            return await todo_repo.get_by_id(todo_id, user_id)
    return run_async(_get_by_id())


@shared_task
async def create_workflow_task(workflow_data):
    from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
    async for db in get_db():
        workflow_repo = WorkflowRepository(db)
        return await workflow_repo.create_workflow(**workflow_data)


@shared_task
async def update_workflow_task(workflow_id, updates):
    from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
    async for db in get_db():
        workflow_repo = WorkflowRepository(db)
        return await workflow_repo.update_workflow(workflow_id, updates)


@shared_task
async def delete_workflow_task(workflow_id):
    from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
    async for db in get_db():
        workflow_repo = WorkflowRepository(db)
        # Implement delete logic here, assuming a delete_workflow method exists
        return await workflow_repo.delete_workflow(workflow_id)


@shared_task
async def get_workflows_task(user_id):
    from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
    async for db in get_db():
        workflow_repo = WorkflowRepository(db)
        return await workflow_repo.get_user_workflows(user_id)


@shared_task
async def get_workflow_by_id_task(workflow_id):
    from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
    async for db in get_db():
        workflow_repo = WorkflowRepository(db)
        return await workflow_repo.get_workflow(workflow_id)

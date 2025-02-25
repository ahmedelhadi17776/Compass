from celery import Celery, shared_task
from Backend.core.config import settings
from Backend.data_layer.database.session import get_db_session
from Backend.data_layer.database.models.task import Task
from Backend.data_layer.repositories.todo_repository import TodoRepository
from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
import asyncio

# Create Celery instance
celery_app = Celery(
    settings.APP_NAME.lower(),
    backend=settings.CELERY_RESULT_BACKEND,
    broker=settings.CELERY_BROKER_URL
)

# Configure Celery using settings
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_store_errors_even_if_ignored=settings.CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED,
    task_send_sent_event=settings.CELERY_TASK_SEND_SENT_EVENT,
    result_expires=settings.CELERY_RESULT_EXPIRES,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    task_acks_late=settings.CELERY_TASK_ACKS_LATE,
    task_reject_on_worker_lost=settings.CELERY_TASK_REJECT_ON_WORKER_LOST,
    task_create_missing_queues=settings.CELERY_TASK_CREATE_MISSING_QUEUES,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_routes={
        "tasks.email_tasks.*": {"queue": "email"},
        "tasks.workflow_tasks.*": {"queue": "workflow"},
        "tasks.ai_tasks.*": {"queue": "ai"},
        "tasks.notification_tasks.*": {"queue": "notification"}
    },
    task_annotations={
        "tasks.email_tasks.send_email": {"rate_limit": "100/m"},
        "tasks.ai_tasks.*": {"rate_limit": "50/m"}
    },
    beat_schedule={
        'check-task-dependencies': {
            'task': 'tasks.task_tasks.check_dependencies',
            'schedule': 300.0,
            'args': None
        }
    }
)

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
    async def _update():
        todo_repo = TodoRepository()
        return await todo_repo.update(todo_id, user_id, **updates)
    return run_async(_update())

@shared_task
def delete_todo_task(todo_id, user_id):
    async def _delete():
        todo_repo = TodoRepository()
        return await todo_repo.delete(todo_id, user_id)
    return run_async(_delete())

@shared_task
def get_todos(user_id):
    async def _get_todos():
        todo_repo = TodoRepository()
        return await todo_repo.get_user_todos(user_id)
    return run_async(_get_todos())

@shared_task
def get_todo_by_id(todo_id, user_id):
    async def _get_by_id():
        todo_repo = TodoRepository()
        return await todo_repo.get_by_id(todo_id, user_id)
    return run_async(_get_by_id())

@shared_task
async def create_workflow_task(workflow_data):
    workflow_repo = WorkflowRepository()
    return await workflow_repo.create_workflow(**workflow_data)

@shared_task
async def update_workflow_task(workflow_id, updates):
    workflow_repo = WorkflowRepository()
    return await workflow_repo.update_workflow(workflow_id, updates)

@shared_task
async def delete_workflow_task(workflow_id):
    workflow_repo = WorkflowRepository()
    return await workflow_repo.delete_workflow(workflow_id)

@shared_task
async def get_workflows_task(user_id):
    workflow_repo = WorkflowRepository()
    return await workflow_repo.get_user_workflows(user_id)

@shared_task
async def get_workflow_by_id_task(workflow_id):
    workflow_repo = WorkflowRepository()
    return await workflow_repo.get_workflow(workflow_id)

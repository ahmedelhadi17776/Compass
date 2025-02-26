from celery import Celery, shared_task
from Backend.core.config import settings
from Backend.data_layer.database.session import get_db_session
from Backend.data_layer.database.models.task import Task
from Backend.data_layer.repositories.todo_repository import TodoRepository
from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
import asyncio
from typing import AsyncGenerator, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.data_layer.database.models.todo import Todo
from Backend.data_layer.database.models.workflow import Workflow

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


def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
        raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Helper function to get a database session."""
    async for session in get_db_session():
        yield session


@shared_task
async def create_todo_task(todo_data: Dict[str, Any]) -> Optional[Todo]:
    async for session in get_session():
        try:
            todo_repo = TodoRepository(session)
            todo = await todo_repo.create(**todo_data)
            await session.commit()
            return todo
        except Exception as e:
            await session.rollback()
            raise e


@shared_task
async def update_todo_task(todo_id: int, user_id: int, updates: Dict[str, Any]) -> Optional[Todo]:
    async for session in get_session():
        try:
            todo_repo = TodoRepository(session)
            todo = await todo_repo.get_by_id(todo_id, user_id)
            if not todo:
                return None
            result = await todo_repo.update(todo_id, user_id, **updates)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            raise e


@shared_task
async def delete_todo_task(todo_id: int, user_id: int) -> bool:
    async for session in get_session():
        try:
            todo_repo = TodoRepository(session)
            todo = await todo_repo.get_by_id(todo_id, user_id)
            if not todo:
                return False
            result = await todo_repo.delete(todo_id, user_id)
            await session.commit()
            return bool(result)
        except Exception as e:
            await session.rollback()
            raise e
    return False


@shared_task
async def get_todos(user_id: int) -> List[Todo]:
    async for session in get_session():
        try:
            todo_repo = TodoRepository(session)
            result = await todo_repo.get_user_todos(user_id)
            return result if result else []
        except Exception as e:
            raise e
    return []


@shared_task
async def get_todo_by_id(todo_id: int, user_id: int) -> Optional[Todo]:
    async for session in get_session():
        try:
            todo_repo = TodoRepository(session)
            result = await todo_repo.get_by_id(todo_id, user_id)
            return result
        except Exception as e:
            raise e


@shared_task
async def create_workflow_task(workflow_data: Dict[str, Any]) -> Optional[Workflow]:
    async for session in get_session():
        try:
            workflow_repo = WorkflowRepository(session)
            result = await workflow_repo.create_workflow(**workflow_data)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            raise e


@shared_task
async def update_workflow_task(workflow_id: int, updates: Dict[str, Any]) -> Optional[Workflow]:
    async for session in get_session():
        try:
            workflow_repo = WorkflowRepository(session)
            result = await workflow_repo.update_workflow(workflow_id, updates)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            raise e


@shared_task
async def delete_workflow_task(workflow_id: int) -> bool:
    async for session in get_session():
        try:
            workflow_repo = WorkflowRepository(session)
            result = await workflow_repo.delete_workflow(workflow_id)
            await session.commit()
            return bool(result)
        except Exception as e:
            await session.rollback()
            raise e
    return False


@shared_task
async def get_workflows_task(user_id: int) -> List[Workflow]:
    async for session in get_session():
        try:
            workflow_repo = WorkflowRepository(session)
            result = await workflow_repo.get_user_workflows(user_id)
            return result if result else []
        except Exception as e:
            raise e
    return []


@shared_task
async def get_workflow_by_id_task(workflow_id: int) -> Optional[Workflow]:
    async for session in get_session():
        try:
            workflow_repo = WorkflowRepository(session)
            result = await workflow_repo.get_workflow(workflow_id)
            return result
        except Exception as e:
            raise e

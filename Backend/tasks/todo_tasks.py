from Backend.core.celery_app import celery_app
from Backend.services.todo_service import TodoService
from datetime import datetime, timedelta
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.database.connection import get_db
from typing import List, Dict, Any, Optional
from Backend.data_layer.database.models.todo import Todo


@celery_app.task
async def get_due_todos() -> List[Dict[str, Any]]:
    """Retrieve due todos for all users."""
    result: List[Dict[str, Any]] = []
    async for db in get_db():
        todo_service = TodoService(repository=TaskRepository(db))
        todos: Optional[List[Todo]] = await todo_service.get_due_todos()
        if todos:
            result.extend([dict(todo.__dict__) for todo in todos])
    return result


@celery_app.task
async def check_due_todos() -> List[Any]:
    """Check for due todos and send notifications"""
    result: List[Any] = []
    async for db in get_db():
        todo_service = TodoService(repository=TaskRepository(db))
        due_todos: Optional[List[Todo]] = await todo_service.get_due_todos()
        if due_todos:
            for todo in due_todos:
                await send_todo_notification.delay(
                    todo.user_id,
                    f"Todo '{todo.title}' is due!",
                    f"Your todo item '{todo.title}' is due at {todo.due_date}"
                )
    return result


@celery_app.task
async def process_recurring_todos():
    """Create new instances of recurring todos"""
    async for db in get_db():
        todo_service = TodoService(repository=TaskRepository(db))
        await todo_service.process_recurring_todos()


@celery_app.task
async def send_todo_notification(user_id: int, title: str, message: str):
    """Send notification for a todo"""
    # Implementation depends on your notification system
    pass

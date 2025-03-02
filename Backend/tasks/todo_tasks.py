from Backend.core.celery_app import celery_app
from Backend.services.todo_service import TodoService
from datetime import datetime, timedelta
from Backend.data_layer.repositories.todo_repository import TodoRepository
from Backend.data_layer.database.connection import get_db
from typing import List, Dict, Any, Optional
from Backend.data_layer.database.models.todo import Todo
from Backend.core.celery_app import get_or_create_eventloop


@celery_app.task
def get_due_todos() -> List[Dict[str, Any]]:
    """Retrieve due todos for all users."""
    async def _get_due():
        result: List[Dict[str, Any]] = []
        async for db in get_db():
            todo_service = TodoService(repository=TodoRepository(db))
            todos: Optional[List[Todo]] = await todo_service.get_due_todos()
            if todos:
                result.extend([todo.to_dict() for todo in todos])
        return result
    loop = get_or_create_eventloop()
    return loop.run_until_complete(_get_due())


@celery_app.task
def check_due_todos() -> List[Any]:
    """Check for due todos and send notifications"""
    async def _check_due():
        result: List[Any] = []
        async for db in get_db():
            todo_service = TodoService(repository=TodoRepository(db))
            due_todos: Optional[List[Todo]] = await todo_service.get_due_todos()
            if due_todos:
                for todo in due_todos:
                    send_todo_notification.delay(
                        todo.user_id,
                        f"Todo '{todo.title}' is due!",
                        f"Your todo item '{todo.title}' is due at {todo.due_date}"
                    )
        return result
    loop = get_or_create_eventloop()
    return loop.run_until_complete(_check_due())


@celery_app.task
def process_recurring_todos():
    """Create new instances of recurring todos"""
    async def _process_recurring():
        async for db in get_db():
            todo_service = TodoService(repository=TodoRepository(db))
            await todo_service.process_recurring_todos()
    loop = get_or_create_eventloop()
    return loop.run_until_complete(_process_recurring())


@celery_app.task
def send_todo_notification(user_id: int, title: str, message: str):
    """Send notification for a todo"""
    # Implementation depends on your notification system
    pass

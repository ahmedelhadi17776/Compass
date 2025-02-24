from Backend.data_layer.repositories.todo_repository import TodoRepository
from Backend.data_layer.cache.redis_client import get_cached_value, set_cached_value, delete_cached_value
from Backend.core.celery_app import (
    create_todo_task,
    update_todo_task,
    delete_todo_task,
    get_todos,
    get_todo_by_id
)
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import json
from Backend.data_layer.repositories.base_repository import BaseRepository
from Backend.data_layer.database.models.todo import Todo


class TodoService:
    def __init__(self, repository: BaseRepository):
        self.repository = repository
        self.cache_ttl = 3600  # 1 hour cache

    async def create_todo(self, **todo_data):
        todo = await create_todo_task.delay(todo_data=todo_data).get()
        await self._invalidate_cache(todo_data['user_id'])
        return todo

    async def get_todo_by_id(self, todo_id: int, user_id: int):
        cache_key = f"todo:{todo_id}:{user_id}"
        cached_todo = await get_cached_value(cache_key)

        if cached_todo:
            return json.loads(cached_todo)

        todo = await get_todo_by_id.delay(todo_id=todo_id, user_id=user_id).get()
        if todo:
            await set_cached_value(cache_key, json.dumps(todo), self.cache_ttl)
        return todo

    async def get_user_todos(self, user_id: int, status: Optional[str] = None):
        cache_key = f"user_todos:{user_id}:{status or 'all'}"
        cached_todos = await get_cached_value(cache_key)

        if cached_todos:
            return json.loads(cached_todos)

        todos = await get_todos.delay(user_id=user_id).get()
        await set_cached_value(cache_key, json.dumps(todos), self.cache_ttl)
        return todos

    async def update_todo(self, todo_id: int, user_id: int, **update_data):
        todo = await update_todo_task.delay(todo_id=todo_id, user_id=user_id, updates=update_data).get()
        if todo:
            await self._invalidate_cache(user_id)
        return todo

    async def delete_todo(self, todo_id: int, user_id: int):
        success = await delete_todo_task.delay(todo_id=todo_id, user_id=user_id).get()
        if success:
            await self._invalidate_cache(user_id)
        return success

    async def _invalidate_cache(self, user_id: int):
        # Implement cache invalidation logic here
        cache_keys = [
            f"user_todos:{user_id}:all",
            f"user_todos:{user_id}:pending",
            f"user_todos:{user_id}:completed"
        ]
        for key in cache_keys:
            await delete_cached_value(key)

    async def convert_task_to_todo(self, task):
        todo_data = {
            "user_id": task.user_id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "priority": task.priority,
            "linked_task_id": task.id
        }
        return await self.create_todo(**todo_data)

    async def get_due_todos(self) -> List[Todo]:
        """Retrieve due todos for all users."""
        todos = await self.repository.get_due_todos()
        if todos is None:
            return []  # Return an empty list if None
        # Ensure this returns a list
        return list(todos) if isinstance(todos, list) else []

    async def process_recurring_todos(self):
        """Process recurring todos and create new instances."""
        recurring_todos = await self.repository.get_recurring_todos()
        # Ensure recurring_todos is treated as iterable
        if recurring_todos is None:
            recurring_todos = []  # Set to an empty list if None

        now = datetime.utcnow()

        for todo in recurring_todos:
            pattern = getattr(todo, 'recurrence_pattern', None)
            if not pattern:
                continue

            # daily, weekly, monthly
            frequency = pattern.get("frequency", "daily")
            # every X days/weeks/months
            interval = int(pattern.get("interval", 1))
            next_occurrence = pattern.get("next_occurrence")

            if not next_occurrence:
                # If no next occurrence is set, use the due date
                next_occurrence = getattr(todo, 'due_date', None)
                if not next_occurrence:
                    continue
            else:
                next_occurrence = datetime.fromisoformat(next_occurrence)

            # If next occurrence is in the past, create new instance
            if next_occurrence <= now:
                # Calculate the next occurrence date
                if frequency == "daily":
                    next_date = next_occurrence + timedelta(days=interval)
                elif frequency == "weekly":
                    next_date = next_occurrence + timedelta(weeks=interval)
                elif frequency == "monthly":
                    # Add months by adding days (approximate)
                    next_date = next_occurrence + timedelta(days=30 * interval)
                else:
                    continue  # Skip unknown frequency

                # Create new instance
                new_todo = await self.repository.create_recurring_instance(todo, next_date)
                if new_todo:
                    # Update the next occurrence in the original todo
                    todo_id = getattr(todo, 'id', None)
                    user_id = getattr(todo, 'user_id', None)
                    if todo_id and user_id:
                        await self.repository.update_next_occurrence(todo_id, next_date)
                        await self._invalidate_cache(user_id)

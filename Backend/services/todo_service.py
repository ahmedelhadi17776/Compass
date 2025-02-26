from Backend.data_layer.repositories.todo_repository import TodoRepository
from Backend.data_layer.cache.redis_client import get_cached_value, set_cached_value, delete_cached_value
from Backend.core.celery_app import (
    create_todo_task,
    update_todo_task,
    delete_todo_task,
    get_todos,
    get_todo_by_id
)
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
from Backend.data_layer.repositories.base_repository import BaseRepository
from Backend.data_layer.database.models.todo import Todo


class TodoService:
    def __init__(self, repository: BaseRepository):
        self.repository = repository
        self.cache_ttl = 3600  # 1 hour cache

    async def create_todo(self, **todo_data) -> Optional[Todo]:
        todo = await create_todo_task(todo_data)
        if todo:
            await self._invalidate_cache(todo_data['user_id'])
        return todo

    async def get_todo_by_id(self, todo_id: int, user_id: int) -> Optional[Todo]:
        cache_key = f"todo:{todo_id}:{user_id}"
        cached_todo = await get_cached_value(cache_key)

        if cached_todo:
            todo_dict = json.loads(cached_todo)
            return Todo(**todo_dict)

        todo = await get_todo_by_id(todo_id, user_id)
        if todo:
            todo_dict = todo.to_dict()
            await set_cached_value(cache_key, json.dumps(todo_dict), self.cache_ttl)
        return todo

    async def get_user_todos(self, user_id: int, status: Optional[str] = None) -> List[Todo]:
        cache_key = f"user_todos:{user_id}:{status or 'all'}"
        cached_todos = await get_cached_value(cache_key)

        if cached_todos:
            todos_list = json.loads(cached_todos)
            return [Todo(**todo_dict) for todo_dict in todos_list]

        todos = await get_todos(user_id)
        if todos:
            todos_list = [todo.to_dict() for todo in todos]
            await set_cached_value(cache_key, json.dumps(todos_list), self.cache_ttl)
        return todos if todos else []

    async def update_todo(self, todo_id: int, user_id: int, **update_data) -> Optional[Todo]:
        todo = await update_todo_task(todo_id, user_id, update_data)
        if todo:
            await self._invalidate_cache(user_id)
        return todo

    async def delete_todo(self, todo_id: int, user_id: int) -> bool:
        success = await delete_todo_task(todo_id, user_id)
        if success:
            await self._invalidate_cache(user_id)
        return success

    async def _invalidate_cache(self, user_id: int) -> None:
        cache_keys = [
            f"user_todos:{user_id}:all",
            f"user_todos:{user_id}:pending",
            f"user_todos:{user_id}:completed"
        ]
        for key in cache_keys:
            await delete_cached_value(key)

    async def convert_task_to_todo(self, task) -> Optional[Todo]:
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
        todos = await self.repository.get_due_todos()
        if todos is None:
            return []
        return list(todos) if isinstance(todos, list) else []

    async def process_recurring_todos(self) -> Optional[Todo]:
        recurring_todos = await self.repository.get_recurring_todos()
        if recurring_todos is None:
            recurring_todos = []

        now = datetime.utcnow()

        for todo in recurring_todos:
            pattern = getattr(todo, 'recurrence_pattern', None)
            if not pattern:
                continue

            frequency = pattern.get("frequency", "daily")
            interval = int(pattern.get("interval", 1))
            next_occurrence = pattern.get("next_occurrence")

            if not next_occurrence:
                next_occurrence = getattr(todo, 'due_date', None)
                if not next_occurrence:
                    continue
            else:
                next_occurrence = datetime.fromisoformat(next_occurrence)

            if next_occurrence <= now:
                if frequency == "daily":
                    next_date = next_occurrence + timedelta(days=interval)
                elif frequency == "weekly":
                    next_date = next_occurrence + timedelta(weeks=interval)
                elif frequency == "monthly":
                    next_date = next_occurrence + timedelta(days=30 * interval)
                else:
                    continue

                new_todo = await self.repository.create_recurring_instance(todo, next_date)
                if new_todo:
                    todo_id = getattr(todo, 'id', None)
                    user_id = getattr(todo, 'user_id', None)
                    if todo_id and user_id:
                        await self.repository.update_next_occurrence(todo_id, next_date)
                        await self._invalidate_cache(user_id)
                return new_todo
        return None

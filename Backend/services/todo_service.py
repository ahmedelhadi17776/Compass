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
            # Convert ISO format datetime strings back to datetime objects
            if 'completion_date' in todo_dict:
                if todo_dict['completion_date']:
                    # Set _completion_date directly instead of completion_date to avoid the property setter validation
                    todo_dict['_completion_date'] = datetime.fromisoformat(
                        todo_dict['completion_date'])
                else:
                    todo_dict['_completion_date'] = None
                del todo_dict['completion_date']
            if 'due_date' in todo_dict and todo_dict['due_date']:
                todo_dict['due_date'] = datetime.fromisoformat(
                    todo_dict['due_date'])
            if 'reminder_time' in todo_dict and todo_dict['reminder_time']:
                todo_dict['reminder_time'] = datetime.fromisoformat(
                    todo_dict['reminder_time'])
            if 'created_at' in todo_dict and todo_dict['created_at']:
                todo_dict['created_at'] = datetime.fromisoformat(
                    todo_dict['created_at'])
            if 'updated_at' in todo_dict and todo_dict['updated_at']:
                todo_dict['updated_at'] = datetime.fromisoformat(
                    todo_dict['updated_at'])
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
            result_todos = []
            for todo_dict in todos_list:
                # Convert ISO format datetime strings back to datetime objects
                if 'completion_date' in todo_dict:
                    if todo_dict['completion_date']:
                        todo_dict['_completion_date'] = datetime.fromisoformat(
                            todo_dict['completion_date'])
                    else:
                        todo_dict['_completion_date'] = None
                    del todo_dict['completion_date']
                if 'due_date' in todo_dict and todo_dict['due_date']:
                    todo_dict['due_date'] = datetime.fromisoformat(
                        todo_dict['due_date'])
                if 'reminder_time' in todo_dict and todo_dict['reminder_time']:
                    todo_dict['reminder_time'] = datetime.fromisoformat(
                        todo_dict['reminder_time'])
                if 'created_at' in todo_dict and todo_dict['created_at']:
                    todo_dict['created_at'] = datetime.fromisoformat(
                        todo_dict['created_at'])
                if 'updated_at' in todo_dict and todo_dict['updated_at']:
                    todo_dict['updated_at'] = datetime.fromisoformat(
                        todo_dict['updated_at'])
                result_todos.append(Todo(**todo_dict))
            return result_todos

        todos = await get_todos(user_id, status)
        if todos:
            todos_list = [todo.to_dict() for todo in todos]
            await set_cached_value(cache_key, json.dumps(todos_list), self.cache_ttl)
        return todos if todos else []

    async def update_todo(self, todo_id: int, user_id: int, **update_data) -> Optional[Todo]:
        todo = await update_todo_task(todo_id, user_id, update_data)
        if todo:
            await self._invalidate_cache(user_id, todo_id)
        return todo

    async def delete_todo(self, todo_id: int, user_id: int) -> bool:
        success = await delete_todo_task(todo_id, user_id)
        if success:
            await self._invalidate_cache(user_id, todo_id)
        return success

    async def _invalidate_cache(self, user_id: int, todo_id: int = None) -> None:
        cache_keys = [
            f"user_todos:{user_id}:all",
            f"user_todos:{user_id}:pending",
            f"user_todos:{user_id}:completed"
        ]

        # Also invalidate the specific todo cache if todo_id is provided
        if todo_id is not None:
            cache_keys.append(f"todo:{todo_id}:{user_id}")

        for key in cache_keys:
            await delete_cached_value(key)

    async def convert_task_to_todo(self, task) -> Optional[Todo]:
        # Handle both dictionary and Task model inputs
        todo_data = {
            "user_id": task.get('creator_id') if isinstance(task, dict) else task.creator_id,
            "title": task.get('title') if isinstance(task, dict) else task.title,
            "description": task.get('description') if isinstance(task, dict) else task.description,
            "priority": task.get('priority') if isinstance(task, dict) else task.priority,
            "linked_task_id": task.get('id') if isinstance(task, dict) else task.id
        }

        # Handle due_date conversion
        due_date = task.get('due_date') if isinstance(task, dict) else task.due_date
        if due_date:
            if isinstance(due_date, str):
                todo_data['due_date'] = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            else:
                todo_data['due_date'] = due_date

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

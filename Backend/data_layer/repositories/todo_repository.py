from Backend.data_layer.database.models.todo import Todo, TodoStatus
from Backend.data_layer.database.connection import get_db
from sqlalchemy.future import select
from sqlalchemy import and_, update
from typing import Optional, List
from datetime import datetime, timedelta
from Backend.data_layer.repositories.base_repository import BaseRepository


class TodoRepository(BaseRepository):
    async def create(self, **todo_data):
        async for db in get_db():
            # Remove any dependencies field if present
            if 'dependencies' in todo_data:
                del todo_data['dependencies']
            new_todo = Todo(**todo_data)
            db.add(new_todo)
            await db.commit()
            await db.refresh(new_todo)
            return new_todo

    async def get_by_id(self, todo_id: int, user_id: Optional[int] = None) -> Optional[Todo]:
        """Get a todo by ID with optional user ID check."""
        async for db in get_db():
            query = select(Todo).where(Todo.id == todo_id)
            if user_id:
                query = query.where(Todo.user_id == user_id)
            result = await db.execute(query)
            return result.scalars().first()

    async def get_user_todos(self, user_id: int, status: Optional[TodoStatus] = None):
        async for db in get_db():
            query = select(Todo).where(Todo.user_id == user_id)
            if status:
                query = query.where(Todo.status == status)
            result = await db.execute(query)
            return result.scalars().all()

    async def update(self, todo_id: int, user_id: int, **update_data):
        async for db in get_db():
            todo = await self.get_by_id(todo_id, user_id)
            if todo:
                for key, value in update_data.items():
                    setattr(todo, key, value)
                if 'status' in update_data and update_data['status'] == TodoStatus.COMPLETED:
                    if todo.completion_date is None:
                        todo.completion_date = datetime.utcnow()
                await db.commit()
                await db.refresh(todo)
                return todo
            return None

    async def delete(self, todo_id: int, user_id: int):
        async for db in get_db():
            todo = await self.get_by_id(todo_id, user_id)
            if todo:
                await db.delete(todo)
                await db.commit()
                return True
            return False

    async def get_due_todos(self) -> List[Todo]:
        """Get all due todos that are pending or in progress."""
        todos: List[Todo] = []
        async for db in get_db():
            now = datetime.utcnow()
            query = select(Todo).where(
                and_(
                    Todo.due_date <= now,
                    Todo.status.in_(
                        [TodoStatus.PENDING, TodoStatus.IN_PROGRESS])
                )
            )
            result = await db.execute(query)
            todos = list(result.scalars().all()) if result else []
        return todos

    async def get_recurring_todos(self) -> List[Todo]:
        """Get all active recurring todos."""
        async for db in get_db():
            query = select(Todo).where(
                and_(
                    Todo.is_recurring == True,
                    Todo.status.in_(
                        [TodoStatus.PENDING, TodoStatus.IN_PROGRESS])
                )
            )
            result = await db.execute(query)
            return list(result.scalars().all()) if result else []
        return []

    async def create_recurring_instance(self, original_todo: Todo, next_date: datetime) -> Optional[Todo]:
        """Create a new instance of a recurring todo."""
        async for db in get_db():
            try:
                new_todo_data = {
                    "user_id": getattr(original_todo, 'user_id', None),
                    "title": getattr(original_todo, 'title', ''),
                    "description": getattr(original_todo, 'description', ''),
                    "status": TodoStatus.PENDING,
                    "priority": getattr(original_todo, 'priority', None),
                    "due_date": next_date,
                    "reminder_time": next_date - timedelta(hours=1) if getattr(original_todo, 'reminder_time', None) else None,
                    "is_recurring": True,
                    "recurrence_pattern": getattr(original_todo, 'recurrence_pattern', {}),
                    "tags": getattr(original_todo, 'tags', []),
                    "checklist": getattr(original_todo, 'checklist', []),
                    "linked_task_id": getattr(original_todo, 'linked_task_id', None),
                    "linked_calendar_event_id": getattr(original_todo, 'linked_calendar_event_id', None),
                    "ai_generated": getattr(original_todo, 'ai_generated', False),
                    "ai_suggestions": getattr(original_todo, 'ai_suggestions', {}),
                    "created_at": datetime.utcnow()
                }
                new_todo = Todo(**new_todo_data)
                db.add(new_todo)
                await db.commit()
                await db.refresh(new_todo)
                return new_todo
            except Exception:
                await db.rollback()
                return None

    async def update_next_occurrence(self, todo_id: int, next_occurrence: datetime) -> bool:
        """Update the next occurrence date in the recurrence pattern."""
        success = False
        async for db in get_db():
            try:
                todo = await self.get_by_id(todo_id)
                if not todo:
                    return False

                current_pattern = getattr(todo, 'recurrence_pattern', {}) or {}
                new_pattern = dict(current_pattern)
                new_pattern['next_occurrence'] = next_occurrence.isoformat()

                stmt = update(Todo).where(Todo.id == todo_id).values(
                    recurrence_pattern=new_pattern
                )
                await db.execute(stmt)
                await db.commit()
                success = True
            except Exception:
                await db.rollback()
        return success

from Backend.data_layer.database.models.todo import Todo, TodoStatus
from Backend.data_layer.database.connection import get_db
from sqlalchemy.future import select
from sqlalchemy import and_, update, cast, DateTime, JSON, true, Boolean, Integer
from sqlalchemy.sql import expression
from typing import Optional, List, Dict, Any, Sequence, cast as type_cast, TypeVar, Union
from datetime import datetime, timedelta
from Backend.data_layer.repositories.base_repository import TodoBaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, load_only
from sqlalchemy.engine.result import ScalarResult, Result
import logging
import json

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Todo)


class TodoRepository(TodoBaseRepository[T]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **todo_data) -> T:
        """Create a new todo."""
        new_todo = Todo(**todo_data)
        self.db.add(new_todo)
        await self.db.flush()
        await self.db.refresh(new_todo)
        return type_cast(T, new_todo)

    async def get_by_id(self, todo_id: int, user_id: Optional[int] = None) -> Optional[T]:
        """Get a todo by ID with optional user ID check."""
        query = select(Todo).where(Todo.id == todo_id)
        if user_id is not None:
            query = query.where(Todo.user_id == user_id)
        result = await self.db.execute(query)
        todo = result.unique().scalar_one_or_none()
        return type_cast(Optional[T], todo)

    async def get_user_todos(self, user_id: int, status: Optional[TodoStatus] = None) -> List[T]:
        """Get all todos for a user with optional status filter."""
        query = select(Todo).where(Todo.user_id == user_id)
        if status is not None:
            query = query.where(Todo.status == status)
        result = await self.db.execute(query)
        todos = result.unique().scalars().all()
        return [type_cast(T, todo) for todo in todos]

    async def update(self, todo_id: int, user_id: int, **update_data) -> Optional[T]:
        """Update a todo."""
        todo = await self.get_by_id(todo_id, user_id)
        if todo:
            for key, value in update_data.items():
                setattr(todo, key, value)
            if 'status' in update_data and update_data['status'] == TodoStatus.COMPLETED:
                todo.completion_date = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(todo)
            return todo
        return None

    async def delete(self, todo_id: int, user_id: int) -> bool:
        """Delete a todo."""
        todo = await self.get_by_id(todo_id, user_id)
        if todo:
            await self.db.delete(todo)
            return True
        return False

    async def get_due_todos(self) -> List[T]:
        """Get all due todos that are pending or in progress."""
        now = datetime.utcnow()
        query = select(Todo).where(
            and_(
                Todo.due_date <= now,
                Todo.status.in_([TodoStatus.PENDING, TodoStatus.IN_PROGRESS])
            )
        )
        result = await self.db.execute(query)
        todos = result.unique().scalars().all()
        return [type_cast(T, todo) for todo in todos]

    async def get_recurring_todos(self) -> List[T]:
        """Get all active recurring todos."""
        query = select(Todo).where(
            and_(
                Todo.is_recurring.is_(expression.true()),
                Todo.status.in_([TodoStatus.PENDING, TodoStatus.IN_PROGRESS])
            )
        )
        result = await self.db.execute(query)
        todos = result.unique().scalars().all()
        return [type_cast(T, todo) for todo in todos]

    async def create_recurring_instance(self, original_todo: T, next_date: datetime) -> Optional[T]:
        """Create a new instance of a recurring todo."""
        try:
            # Load the todo object with all necessary attributes
            query = select(Todo).where(Todo.id == original_todo.id)
            result = await self.db.execute(query)
            todo = result.unique().scalar_one_or_none()
            if not todo:
                return None

            # Convert SQLAlchemy model to dict for new instance
            recurrence_pattern = json.loads(json.dumps(
                getattr(todo, 'recurrence_pattern', None) or {}))
            tags = json.loads(json.dumps(getattr(todo, 'tags', None) or {}))
            checklist = json.loads(json.dumps(
                getattr(todo, 'checklist', None) or {}))
            ai_suggestions = json.loads(json.dumps(
                getattr(todo, 'ai_suggestions', None) or {}))
            reminder_time = getattr(todo, 'reminder_time', None)

            new_todo_data = {
                "user_id": todo.user_id,
                "title": todo.title,
                "description": todo.description,
                "status": TodoStatus.PENDING,
                "priority": todo.priority,
                "due_date": next_date,
                "reminder_time": next_date - timedelta(hours=1) if reminder_time else None,
                "is_recurring": True,
                "recurrence_pattern": recurrence_pattern,
                "tags": tags,
                "checklist": checklist,
                "linked_task_id": todo.linked_task_id,
                "linked_calendar_event_id": todo.linked_calendar_event_id,
                "ai_generated": bool(todo.ai_generated),
                "ai_suggestions": ai_suggestions
            }
            return await self.create(**new_todo_data)
        except Exception as e:
            logger.error(f"Error creating recurring instance: {str(e)}")
            await self.db.rollback()
            return None

    async def update_next_occurrence(self, todo_id: int, next_occurrence: datetime) -> bool:
        """Update the next occurrence date in the recurrence pattern."""
        try:
            # Load the todo object
            query = select(Todo).where(Todo.id == todo_id)
            result = await self.db.execute(query)
            todo = result.unique().scalar_one_or_none()
            if not todo:
                return False

            # Convert SQLAlchemy model to dict for update
            pattern = json.loads(json.dumps(
                getattr(todo, 'recurrence_pattern', None) or {}))
            pattern['next_occurrence'] = next_occurrence.isoformat()

            stmt = (
                update(Todo)
                .where(Todo.id == todo_id)
                .values(recurrence_pattern=pattern)
            )
            await self.db.execute(stmt)
            return True
        except Exception as e:
            logger.error(f"Error updating next occurrence: {str(e)}")
            await self.db.rollback()
            return False

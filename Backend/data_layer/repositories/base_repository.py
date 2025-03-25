from abc import ABC, abstractmethod
from typing import Optional, List, TypeVar, Generic, Any
from datetime import datetime

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Base repository interface for all entities."""

    @abstractmethod
    async def create(self, **data) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    async def get_by_id(self, id: int, user_id: Optional[int] = None) -> Optional[T]:
        """Get an entity by ID."""
        pass

    @abstractmethod
    async def update(self, id: int, user_id: int, **data) -> Optional[T]:
        """Update an entity."""
        pass

    @abstractmethod
    async def delete(self, id: int, user_id: int) -> bool:
        """Delete an entity."""
        pass


class TodoBaseRepository(BaseRepository[T]):
    """Base repository interface for todo-specific functionality."""

    @abstractmethod
    async def get_due_todos(self) -> List[T]:
        """Get all due todos."""
        pass

    @abstractmethod
    async def get_recurring_todos(self) -> List[T]:
        """Get all recurring todos."""
        pass

    @abstractmethod
    async def create_recurring_instance(self, original_todo: T, next_date: datetime) -> Optional[T]:
        """Create a new instance of a recurring todo."""
        pass

    @abstractmethod
    async def update_next_occurrence(self, todo_id: int, next_occurrence: datetime) -> bool:
        """Update the next occurrence date."""
        pass

    async def get_all(self):
        raise NotImplementedError

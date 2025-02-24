from abc import ABC, abstractmethod
from datetime import datetime


class BaseRepository(ABC):
    @abstractmethod
    async def create(self, **data):
        pass

    @abstractmethod
    async def get_by_id(self, id: int):
        pass

    @abstractmethod
    async def update(self, id: int, **updates):
        pass

    @abstractmethod
    async def delete(self, id: int):
        pass

    @abstractmethod
    async def get_due_todos(self):
        pass

    @abstractmethod
    async def get_recurring_todos(self):
        pass

    @abstractmethod
    async def create_recurring_instance(self, original_todo, next_date):
        pass

    @abstractmethod
    async def update_next_occurrence(self, todo_id: int, next_occurrence: datetime):
        pass

    async def get_all(self):
        raise NotImplementedError

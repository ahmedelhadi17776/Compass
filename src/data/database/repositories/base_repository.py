from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.data.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: int) -> Optional[ModelType]:
        """Get a record by ID."""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[ModelType]:
        """Get all records."""
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj_in: ModelType) -> ModelType:
        """Create a new record."""
        self.session.add(obj_in)
        await self.session.commit()
        await self.session.refresh(obj_in)
        return obj_in

    async def update(self, obj: ModelType) -> ModelType:
        """Update a record."""
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: int) -> bool:
        """Delete a record."""
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.data_layer.database.models.organization import Organization
from Backend.data_layer.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)

class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **org_data) -> Organization:
        """Create a new organization."""
        new_org = Organization(**org_data)
        self.db.add(new_org)
        await self.db.flush()
        return new_org

    async def get_by_id(self, org_id: int) -> Optional[Organization]:
        """Get an organization by ID."""
        query = select(Organization).where(Organization.id == org_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get all organizations with pagination."""
        query = select(Organization).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, org_id: int, **update_data) -> Optional[Organization]:
        """Update an organization."""
        org = await self.get_by_id(org_id)
        if org:
            for key, value in update_data.items():
                setattr(org, key, value)
            await self.db.flush()
        return org

    async def delete(self, org_id: int) -> bool:
        """Delete an organization."""
        org = await self.get_by_id(org_id)
        if org:
            await self.db.delete(org)
            return True
        return False

    async def get_by_name(self, name: str) -> Optional[Organization]:
        """Get an organization by name."""
        query = select(Organization).where(Organization.name == name)
        result = await self.db.execute(query)
        return result.scalars().first()
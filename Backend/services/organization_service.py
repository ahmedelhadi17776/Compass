from typing import List, Optional, Dict
from Backend.data_layer.repositories.organization_repository import OrganizationRepository
from Backend.data_layer.database.models.organization import Organization
import logging

logger = logging.getLogger(__name__)

class OrganizationService:
    def __init__(self, repository: OrganizationRepository):
        self.repository = repository

    async def create_organization(self, **org_data) -> Organization:
        """Create a new organization."""
        return await self.repository.create(**org_data)

    async def get_organization(self, org_id: int) -> Optional[Organization]:
        """Get an organization by ID."""
        return await self.repository.get_by_id(org_id)

    async def get_organizations(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get all organizations."""
        return await self.repository.get_all(skip=skip, limit=limit)

    async def update_organization(self, org_id: int, org_data: Dict) -> Optional[Organization]:
        """Update an organization."""
        return await self.repository.update(org_id, **org_data)

    async def delete_organization(self, org_id: int) -> bool:
        """Delete an organization."""
        return await self.repository.delete(org_id)

    async def get_organization_details(self, org_id: int) -> Optional[Dict]:
        """Get organization with additional details."""
        org = await self.repository.get_by_id(org_id)
        if not org:
            return None
        
        return {
            "id": org.id,
            "name": org.name,
            "description": org.description,
            "created_at": org.created_at,
            "updated_at": org.updated_at,
            "projects_count": len(org.projects),
            "users_count": len(org.users),
            "tasks_count": len(org.tasks),
            "workflows_count": len(org.workflows)
        }
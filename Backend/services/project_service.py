from typing import List, Optional, Dict
from Backend.data_layer.repositories.project_repository import ProjectRepository
from Backend.data_layer.database.models.project import Project, ProjectMember
import logging

logger = logging.getLogger(__name__)

class ProjectService:
    def __init__(self, repository: ProjectRepository):
        self.repository = repository

    async def create_project(self, **project_data) -> Project:
        """Create a new project."""
        return await self.repository.create(**project_data)

    async def get_project(self, project_id: int, organization_id: Optional[int] = None) -> Optional[Project]:
        """Get a project by ID."""
        return await self.repository.get_by_id(project_id, organization_id)

    async def get_projects(
        self,
        organization_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Get all projects."""
        return await self.repository.get_all(organization_id, skip, limit)

    async def update_project(self, project_id: int, organization_id: int, project_data: Dict) -> Optional[Project]:
        """Update a project."""
        return await self.repository.update(project_id, organization_id, **project_data)

    async def delete_project(self, project_id: int, organization_id: int) -> bool:
        """Delete a project."""
        return await self.repository.delete(project_id, organization_id)

    async def get_project_details(self, project_id: int) -> Optional[Dict]:
        """Get project with additional details."""
        project = await self.repository.get_project_with_details(project_id)
        if not project:
            return None
        
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "organization_id": project.organization_id,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "members_count": len(project.members),
            "tasks_count": len(project.tasks),
            "members": [
                {
                    "user_id": member.user_id,
                    "role": member.role,
                    "joined_at": member.joined_at
                }
                for member in project.members
            ]
        }

    async def add_project_member(self, project_id: int, user_id: int, role: str) -> ProjectMember:
        """Add a member to the project."""
        return await self.repository.add_member(project_id, user_id, role)

    async def remove_project_member(self, project_id: int, user_id: int) -> bool:
        """Remove a member from the project."""
        return await self.repository.remove_member(project_id, user_id)
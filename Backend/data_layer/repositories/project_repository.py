from typing import List, Optional, Dict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from Backend.data_layer.database.models.project import Project, ProjectMember
from Backend.data_layer.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **project_data) -> Project:
        """Create a new project."""
        new_project = Project(**project_data)
        self.db.add(new_project)
        await self.db.flush()
        return new_project

    async def get_by_id(self, project_id: int, organization_id: Optional[int] = None) -> Optional[Project]:
        """Get a project by ID with optional organization check."""
        query = select(Project).where(Project.id == project_id)
        if organization_id:
            query = query.where(Project.organization_id == organization_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all(
        self,
        organization_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Get all projects with optional organization filter."""
        query = select(Project)
        if organization_id:
            query = query.where(Project.organization_id == organization_id)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, project_id: int, organization_id: int, **update_data) -> Optional[Project]:
        """Update a project."""
        project = await self.get_by_id(project_id, organization_id)
        if project:
            for key, value in update_data.items():
                setattr(project, key, value)
            await self.db.flush()
        return project

    async def delete(self, project_id: int, organization_id: int) -> bool:
        """Delete a project."""
        project = await self.get_by_id(project_id, organization_id)
        if project:
            await self.db.delete(project)
            return True
        return False

    async def get_project_with_details(self, project_id: int) -> Optional[Project]:
        """Get project with all related details."""
        query = (
            select(Project)
            .options(
                joinedload(Project.members),
                joinedload(Project.tasks)
            )
            .where(Project.id == project_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def add_member(self, project_id: int, user_id: int, role: str) -> ProjectMember:
        """Add a member to the project."""
        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        self.db.add(member)
        await self.db.flush()
        return member

    async def remove_member(self, project_id: int, user_id: int) -> bool:
        """Remove a member from the project."""
        query = select(ProjectMember).where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        member = result.scalars().first()
        if member:
            await self.db.delete(member)
            return True
        return False
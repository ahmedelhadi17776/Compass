from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from Backend.data_layer.database.connection import get_db
from Backend.app.schemas.project_schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectWithDetails,
    ProjectMemberCreate,
    ProjectMemberResponse
)
from Backend.services.project_service import ProjectService
from Backend.data_layer.repositories.project_repository import ProjectRepository
from Backend.api.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new project."""
    try:
        repo = ProjectRepository(db)
        service = ProjectService(repo)
        project_data = project.dict()
        project_data["creator_id"] = current_user.id
        result = await service.create_project(**project_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project: {str(e)}"
        )

@router.get("/{project_id}", response_model=ProjectWithDetails)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get project details."""
    repo = ProjectRepository(db)
    service = ProjectService(repo)
    project = await service.get_project_details(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    return project

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    organization_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all projects."""
    repo = ProjectRepository(db)
    service = ProjectService(repo)
    return await service.get_projects(organization_id, skip, limit)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a project."""
    try:
        repo = ProjectRepository(db)
        service = ProjectService(repo)
        
        project = await service.update_project(
            project_id,
            current_user.organization_id,
            project_update.dict(exclude_unset=True)
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        return project
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating project: {str(e)}"
        )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a project."""
    repo = ProjectRepository(db)
    service = ProjectService(repo)
    
    success = await service.delete_project(project_id, current_user.organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return {"message": "Project deleted successfully"}

@router.post("/{project_id}/members", response_model=ProjectMemberResponse)
async def add_project_member(
    project_id: int,
    member: ProjectMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add a member to the project."""
    try:
        repo = ProjectRepository(db)
        service = ProjectService(repo)
        result = await service.add_project_member(
            project_id=project_id,
            user_id=member.user_id,
            role=member.role
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding project member: {str(e)}"
        )

@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Remove a member from the project."""
    repo = ProjectRepository(db)
    service = ProjectService(repo)
    
    success = await service.remove_project_member(project_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project member not found"
        )
    return {"message": "Project member removed successfully"}
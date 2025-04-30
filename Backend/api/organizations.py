from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from Backend.data_layer.database.connection import get_db
from Backend.app.schemas.organization_schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationWithDetails
)
from Backend.services.organization_service import OrganizationService
from Backend.data_layer.repositories.organization_repository import OrganizationRepository
from Backend.api.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new organization."""
    try:
        repo = OrganizationRepository(db)
        service = OrganizationService(repo)
        result = await service.create_organization(**org.dict())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating organization: {str(e)}"
        )

@router.get("/{org_id}", response_model=OrganizationWithDetails)
async def get_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get organization details."""
    repo = OrganizationRepository(db)
    service = OrganizationService(repo)
    org = await service.get_organization_details(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID {org_id} not found"
        )
    return org

@router.get("/", response_model=List[OrganizationResponse])
async def get_organizations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all organizations."""
    repo = OrganizationRepository(db)
    service = OrganizationService(repo)
    return await service.get_organizations(skip=skip, limit=limit)

@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: int,
    org_update: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an organization."""
    try:
        repo = OrganizationRepository(db)
        service = OrganizationService(repo)
        
        org = await service.update_organization(org_id, org_update.dict(exclude_unset=True))
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with ID {org_id} not found"
            )
        return org
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating organization: {str(e)}"
        )

@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an organization."""
    repo = OrganizationRepository(db)
    service = OrganizationService(repo)
    
    success = await service.delete_organization(org_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return {"message": "Organization deleted successfully"}
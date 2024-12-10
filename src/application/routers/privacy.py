"""Privacy settings and data request router."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.database.session import get_session
from src.data.repositories.privacy_settings_repository import PrivacySettingsRepository
from src.data.repositories.data_request_repository import DataRequestRepository
from src.application.schemas.privacy import (
    PrivacySettings, PrivacySettingsCreate, PrivacySettingsUpdate,
    DataRequest, DataRequestCreate, DataRequestUpdate,
    DataRequestStatus, PrivacyReport
)
from src.core.security import get_current_user
from src.data.database.models.user import User

router = APIRouter(prefix="/privacy", tags=["privacy"])

@router.get("/settings", response_model=PrivacySettings)
async def get_privacy_settings(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get user's privacy settings."""
    repo = PrivacySettingsRepository(session)
    settings = await repo.get_user_settings(current_user.id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Privacy settings not found"
        )
    return settings

@router.post("/settings", response_model=PrivacySettings)
async def create_privacy_settings(
    settings: PrivacySettingsCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Create user's privacy settings."""
    repo = PrivacySettingsRepository(session)
    existing = await repo.get_user_settings(current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Privacy settings already exist"
        )
    return await repo.create_settings(current_user.id, settings.dict())

@router.put("/settings", response_model=PrivacySettings)
async def update_privacy_settings(
    settings: PrivacySettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Update user's privacy settings."""
    repo = PrivacySettingsRepository(session)
    existing = await repo.get_user_settings(current_user.id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Privacy settings not found"
        )
    return await repo.update_settings(current_user.id, settings.dict(exclude_unset=True))

@router.post("/data-requests", response_model=DataRequest)
async def create_data_request(
    request: DataRequestCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Create a new data request."""
    repo = DataRequestRepository(session)
    return await repo.create_request({
        "user_id": current_user.id,
        **request.dict()
    })

@router.get("/data-requests", response_model=List[DataRequest])
async def list_data_requests(
    request_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """List user's data requests."""
    repo = DataRequestRepository(session)
    return await repo.get_user_requests(
        current_user.id,
        request_type=request_type,
        status=status
    )

@router.get("/data-requests/{request_id}", response_model=DataRequest)
async def get_data_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific data request."""
    repo = DataRequestRepository(session)
    request = await repo.get_request(request_id)
    if request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this request"
        )
    return request

@router.put("/data-requests/{request_id}", response_model=DataRequest)
async def update_data_request(
    request_id: int,
    request: DataRequestUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Update a data request."""
    repo = DataRequestRepository(session)
    existing = await repo.get_request(request_id)
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this request"
        )
    return await repo.update_request(request_id, request.dict(exclude_unset=True))

@router.get("/data-requests/{request_id}/status", response_model=DataRequestStatus)
async def get_request_status(
    request_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get the status of a data request."""
    repo = DataRequestRepository(session)
    request = await repo.get_request(request_id)
    if request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this request"
        )
    
    # Calculate estimated completion time based on request type and status
    estimated_completion = None
    if request.status == "processing":
        if request.type == "export":
            estimated_completion = datetime.utcnow() + timedelta(hours=1)
        elif request.type == "deletion":
            estimated_completion = datetime.utcnow() + timedelta(days=1)

    return DataRequestStatus(
        request_id=request.id,
        status=request.status,
        created_at=request.created_at,
        completed_at=request.completed_at,
        estimated_completion=estimated_completion
    )

@router.get("/report", response_model=PrivacyReport)
async def get_privacy_report(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get privacy-related statistics and report."""
    settings_repo = PrivacySettingsRepository(session)
    request_repo = DataRequestRepository(session)

    # Get privacy statistics
    stats = await request_repo.get_privacy_stats()

    return PrivacyReport(
        period={
            "start": datetime.utcnow() - timedelta(days=30),
            "end": datetime.utcnow()
        },
        data_requests=stats,
        privacy_settings=await settings_repo.get_user_settings(current_user.id),
        data_retention={
            "personal_data": "30 days",
            "usage_data": "90 days",
            "analytics": "1 year"
        },
        generated_at=datetime.utcnow()
    )

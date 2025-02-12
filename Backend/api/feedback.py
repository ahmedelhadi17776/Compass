"""Feedback router."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.data.database.session import get_session
from Backend.data.repositories.feedback_repository import FeedbackRepository
from Backend.application.schemas.feedback import (
    Feedback, FeedbackCreate, FeedbackUpdate,
    FeedbackComment, FeedbackCommentCreate,
    FeedbackStats, FeedbackExport
)
from Backend.core.security import get_current_user
from Backend.data.database.models.user import User

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("", response_model=Feedback)
async def create_feedback(
    feedback: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Create new feedback."""
    repo = FeedbackRepository(session)
    return await repo.create_feedback({
        "user_id": current_user.id,
        **feedback.dict()
    })

@router.get("", response_model=List[Feedback])
async def list_feedback(
    type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """List feedback entries."""
    repo = FeedbackRepository(session)
    filters = {}
    if type:
        filters["type"] = type
    if status:
        filters["status"] = status
    if category:
        filters["category"] = category
    return await repo.list_feedback(filters=filters)

@router.get("/{feedback_id}", response_model=Feedback)
async def get_feedback(
    feedback_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get specific feedback."""
    repo = FeedbackRepository(session)
    feedback = await repo.get_feedback(feedback_id)
    if feedback.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this feedback"
        )
    return feedback

@router.put("/{feedback_id}", response_model=Feedback)
async def update_feedback(
    feedback_id: int,
    feedback: FeedbackUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Update feedback."""
    repo = FeedbackRepository(session)
    existing = await repo.get_feedback(feedback_id)
    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this feedback"
        )
    
    update_data = feedback.dict(exclude_unset=True)
    if "status" in update_data and update_data["status"] in ["resolved", "closed"]:
        update_data["resolved_by"] = current_user.id
        update_data["resolved_at"] = datetime.utcnow()
    
    return await repo.update_feedback(feedback_id, update_data)

@router.post("/{feedback_id}/comments", response_model=FeedbackComment)
async def add_comment(
    feedback_id: int,
    comment: FeedbackCommentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Add a comment to feedback."""
    repo = FeedbackRepository(session)
    feedback = await repo.get_feedback(feedback_id)
    if feedback.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to comment on this feedback"
        )
    
    return await repo.add_comment({
        "feedback_id": feedback_id,
        "user_id": current_user.id,
        **comment.dict()
    })

@router.get("/{feedback_id}/comments", response_model=List[FeedbackComment])
async def get_comments(
    feedback_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get comments for feedback."""
    repo = FeedbackRepository(session)
    feedback = await repo.get_feedback(feedback_id)
    if feedback.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view comments for this feedback"
        )
    return await repo.get_comments(feedback_id)

@router.get("/statistics", response_model=FeedbackStats)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get feedback statistics."""
    repo = FeedbackRepository(session)
    return await repo.get_statistics()

@router.get("/export", response_model=FeedbackExport)
async def export_feedback(
    format: str = "json",
    type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Export feedback data."""
    repo = FeedbackRepository(session)
    filters = {}
    if type:
        filters["type"] = type
    if status:
        filters["status"] = status
    if category:
        filters["category"] = category
    return await repo.export_feedback(format=format, filters=filters)

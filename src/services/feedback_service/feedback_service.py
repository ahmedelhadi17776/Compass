"""Feedback service module for handling user feedback and system improvements."""
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ...data.repositories.feedback_repository import FeedbackRepository
from ...data.repositories.user_repository import UserRepository
from ...core.exceptions import FeedbackServiceError

class FeedbackService:
    """Service for managing user feedback and improvement suggestions."""

    def __init__(self, session: AsyncSession):
        """Initialize feedback service."""
        self._feedback_repository = FeedbackRepository(session)
        self._user_repository = UserRepository(session)
        self._session = session

    async def submit_feedback(
        self,
        user_id: int,
        feedback_type: str,
        content: str,
        category: Optional[str] = None,
        context: Optional[Dict] = None,
        priority: str = "normal"
    ) -> Dict:
        """Submit new feedback."""
        try:
            # Validate feedback type
            valid_types = ["bug", "feature_request", "improvement", "general"]
            if feedback_type not in valid_types:
                raise FeedbackServiceError(f"Invalid feedback type. Must be one of: {valid_types}")

            # Validate priority
            valid_priorities = ["low", "normal", "high", "critical"]
            if priority not in valid_priorities:
                raise FeedbackServiceError(f"Invalid priority. Must be one of: {valid_priorities}")

            # Create feedback entry
            feedback_data = {
                "user_id": user_id,
                "type": feedback_type,
                "content": content,
                "category": category,
                "context": context,
                "priority": priority,
                "status": "new"
            }

            feedback = await self._feedback_repository.create_feedback(feedback_data)

            return {
                "id": feedback.id,
                "type": feedback.type,
                "status": feedback.status,
                "submitted_at": feedback.created_at
            }

        except Exception as e:
            raise FeedbackServiceError(f"Error submitting feedback: {str(e)}")

    async def get_feedback(
        self,
        feedback_id: int,
        user_id: Optional[int] = None
    ) -> Dict:
        """Retrieve specific feedback entry."""
        feedback = await self._feedback_repository.get_feedback(feedback_id)
        
        # Check if user has access to this feedback
        if user_id and feedback.user_id != user_id:
            user = await self._user_repository.get_user(user_id)
            if not user.is_admin:
                raise FeedbackServiceError("Unauthorized access to feedback")

        return {
            "id": feedback.id,
            "type": feedback.type,
            "content": feedback.content,
            "category": feedback.category,
            "context": feedback.context,
            "priority": feedback.priority,
            "status": feedback.status,
            "submitted_at": feedback.created_at,
            "last_updated": feedback.updated_at
        }

    async def update_feedback_status(
        self,
        feedback_id: int,
        status: str,
        admin_id: int,
        resolution_notes: Optional[str] = None
    ) -> Dict:
        """Update feedback status."""
        valid_statuses = ["new", "in_progress", "resolved", "closed", "needs_info"]
        if status not in valid_statuses:
            raise FeedbackServiceError(f"Invalid status. Must be one of: {valid_statuses}")

        # Verify admin permissions
        admin = await self._user_repository.get_user(admin_id)
        if not admin.is_admin:
            raise FeedbackServiceError("Unauthorized: Only admins can update feedback status")

        update_data = {
            "status": status,
            "resolution_notes": resolution_notes,
            "resolved_by": admin_id if status in ["resolved", "closed"] else None,
            "resolved_at": datetime.utcnow() if status in ["resolved", "closed"] else None
        }

        feedback = await self._feedback_repository.update_feedback(feedback_id, update_data)
        
        return {
            "id": feedback.id,
            "status": feedback.status,
            "resolution_notes": feedback.resolution_notes,
            "last_updated": feedback.updated_at
        }

    async def list_feedback(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        feedback_type: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """List feedback entries with filtering options."""
        filters = {
            "user_id": user_id,
            "status": status,
            "type": feedback_type,
            "priority": priority,
            "category": category
        }
        
        # Remove None values from filters
        filters = {k: v for k, v in filters.items() if v is not None}
        
        feedback_list = await self._feedback_repository.list_feedback(
            filters=filters,
            limit=limit,
            offset=offset
        )

        total_count = await self._feedback_repository.count_feedback(filters)

        return {
            "items": [
                {
                    "id": f.id,
                    "type": f.type,
                    "content": f.content,
                    "status": f.status,
                    "priority": f.priority,
                    "submitted_at": f.created_at
                }
                for f in feedback_list
            ],
            "total": total_count,
            "limit": limit,
            "offset": offset
        }

    async def add_feedback_comment(
        self,
        feedback_id: int,
        user_id: int,
        comment: str
    ) -> Dict:
        """Add comment to feedback."""
        feedback = await self._feedback_repository.get_feedback(feedback_id)
        
        # Verify user has access to comment
        if feedback.user_id != user_id:
            user = await self._user_repository.get_user(user_id)
            if not user.is_admin:
                raise FeedbackServiceError("Unauthorized to comment on this feedback")

        comment_data = {
            "feedback_id": feedback_id,
            "user_id": user_id,
            "content": comment
        }

        comment = await self._feedback_repository.add_comment(comment_data)

        return {
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at,
            "user_id": comment.user_id
        }

    async def get_feedback_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get feedback statistics."""
        stats = await self._feedback_repository.get_statistics(start_date, end_date)
        
        return {
            "total_feedback": stats["total"],
            "by_type": stats["by_type"],
            "by_status": stats["by_status"],
            "by_priority": stats["by_priority"],
            "resolution_time_avg": stats["resolution_time_avg"],
            "trending_categories": stats["trending_categories"]
        }

    async def export_feedback(
        self,
        format: str = "json",
        filters: Optional[Dict] = None
    ) -> Dict:
        """Export feedback data in specified format."""
        valid_formats = ["json", "csv", "excel"]
        if format not in valid_formats:
            raise FeedbackServiceError(f"Invalid export format. Must be one of: {valid_formats}")

        feedback_data = await self._feedback_repository.export_feedback(
            format=format,
            filters=filters
        )

        return {
            "format": format,
            "data": feedback_data,
            "exported_at": datetime.utcnow()
        }

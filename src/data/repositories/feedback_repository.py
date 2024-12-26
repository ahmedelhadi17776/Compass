"""Feedback repository module."""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.feedback import Feedback
from ..database.models.feedback_comment import FeedbackComment
from core.exceptions import FeedbackNotFoundError

class FeedbackRepository:
    """Repository for managing feedback."""

    def __init__(self, session: AsyncSession):
        """Initialize feedback repository."""
        self._session = session

    async def create_feedback(self, feedback_data: Dict) -> Feedback:
        """Create a new feedback entry."""
        feedback = Feedback(
            user_id=feedback_data["user_id"],
            type=feedback_data["type"],
            content=feedback_data["content"],
            category=feedback_data.get("category"),
            context=feedback_data.get("context"),
            priority=feedback_data.get("priority", "normal"),
            status=feedback_data.get("status", "new"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self._session.add(feedback)
        await self._session.commit()
        await self._session.refresh(feedback)
        return feedback

    async def get_feedback(self, feedback_id: int) -> Feedback:
        """Get a specific feedback entry."""
        feedback = await self._session.execute(
            select(Feedback).where(Feedback.id == feedback_id)
        )
        feedback = feedback.scalar_one_or_none()
        if not feedback:
            raise FeedbackNotFoundError(f"Feedback with id {feedback_id} not found")
        return feedback

    async def update_feedback(
        self,
        feedback_id: int,
        feedback_data: Dict
    ) -> Feedback:
        """Update a feedback entry."""
        feedback = await self.get_feedback(feedback_id)
        for key, value in feedback_data.items():
            if hasattr(feedback, key):
                setattr(feedback, key, value)
        feedback.updated_at = datetime.utcnow()
        await self._session.commit()
        await self._session.refresh(feedback)
        return feedback

    async def list_feedback(
        self,
        filters: Optional[Dict] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Feedback]:
        """List feedback entries with filtering."""
        query = select(Feedback)
        
        if filters:
            for key, value in filters.items():
                if hasattr(Feedback, key):
                    query = query.where(getattr(Feedback, key) == value)

        query = query.order_by(desc(Feedback.created_at)).offset(offset).limit(limit)
        feedback_list = await self._session.execute(query)
        return feedback_list.scalars().all()

    async def count_feedback(self, filters: Optional[Dict] = None) -> int:
        """Count total feedback entries with filtering."""
        query = select(func.count()).select_from(Feedback)
        
        if filters:
            for key, value in filters.items():
                if hasattr(Feedback, key):
                    query = query.where(getattr(Feedback, key) == value)

        result = await self._session.execute(query)
        return result.scalar_one()

    async def add_comment(self, comment_data: Dict) -> FeedbackComment:
        """Add a comment to feedback."""
        comment = FeedbackComment(
            feedback_id=comment_data["feedback_id"],
            user_id=comment_data["user_id"],
            content=comment_data["content"],
            created_at=datetime.utcnow()
        )
        self._session.add(comment)
        await self._session.commit()
        await self._session.refresh(comment)
        return comment

    async def get_comments(self, feedback_id: int) -> List[FeedbackComment]:
        """Get all comments for a feedback entry."""
        comments = await self._session.execute(
            select(FeedbackComment)
            .where(FeedbackComment.feedback_id == feedback_id)
            .order_by(FeedbackComment.created_at)
        )
        return comments.scalars().all()

    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get feedback statistics."""
        query = select(Feedback)
        if start_date:
            query = query.where(Feedback.created_at >= start_date)
        if end_date:
            query = query.where(Feedback.created_at <= end_date)

        feedback_entries = await self._session.execute(query)
        feedback_entries = feedback_entries.scalars().all()

        # Calculate statistics
        total = len(feedback_entries)
        by_type = {}
        by_status = {}
        by_priority = {}
        resolution_times = []
        categories = {}

        for feedback in feedback_entries:
            # Count by type
            by_type[feedback.type] = by_type.get(feedback.type, 0) + 1
            
            # Count by status
            by_status[feedback.status] = by_status.get(feedback.status, 0) + 1
            
            # Count by priority
            by_priority[feedback.priority] = by_priority.get(feedback.priority, 0) + 1
            
            # Calculate resolution time for resolved items
            if feedback.status in ["resolved", "closed"] and feedback.resolved_at:
                resolution_time = (
                    feedback.resolved_at - feedback.created_at
                ).total_seconds()
                resolution_times.append(resolution_time)

            # Count categories
            if feedback.category:
                categories[feedback.category] = categories.get(feedback.category, 0) + 1

        # Calculate average resolution time
        avg_resolution_time = (
            sum(resolution_times) / len(resolution_times)
            if resolution_times else 0
        )

        # Sort categories by frequency
        trending_categories = sorted(
            categories.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "total": total,
            "by_type": by_type,
            "by_status": by_status,
            "by_priority": by_priority,
            "resolution_time_avg": avg_resolution_time,
            "trending_categories": dict(trending_categories)
        }

    async def export_feedback(
        self,
        format: str = "json",
        filters: Optional[Dict] = None
    ) -> Dict:
        """Export feedback data in specified format."""
        feedback_entries = await self.list_feedback(filters=filters, limit=1000)
        
        export_data = []
        for feedback in feedback_entries:
            comments = await self.get_comments(feedback.id)
            export_data.append({
                "id": feedback.id,
                "type": feedback.type,
                "content": feedback.content,
                "category": feedback.category,
                "priority": feedback.priority,
                "status": feedback.status,
                "created_at": feedback.created_at.isoformat(),
                "resolved_at": (
                    feedback.resolved_at.isoformat()
                    if feedback.resolved_at else None
                ),
                "comments": [
                    {
                        "user_id": comment.user_id,
                        "content": comment.content,
                        "created_at": comment.created_at.isoformat()
                    }
                    for comment in comments
                ]
            })

        return {
            "format": format,
            "data": export_data,
            "exported_at": datetime.utcnow().isoformat()
        }

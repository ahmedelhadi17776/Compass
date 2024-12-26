"""Data request repository module."""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.data_request import DataRequest
from ..database.models.data_archive import DataArchive
from core.exceptions import DataRequestNotFoundError

class DataRequestRepository:
    """Repository for managing data requests and archives."""

    def __init__(self, session: AsyncSession):
        """Initialize data request repository."""
        self._session = session

    async def create_request(self, request_data: Dict) -> DataRequest:
        """Create a new data request."""
        request = DataRequest(
            user_id=request_data["user_id"],
            type=request_data["type"],
            data_types=request_data["data_types"],
            reason=request_data.get("reason"),
            status=request_data.get("status", "pending"),
            created_at=datetime.utcnow()
        )
        self._session.add(request)
        await self._session.commit()
        await self._session.refresh(request)
        return request

    async def get_request(self, request_id: int) -> DataRequest:
        """Get a specific data request."""
        request = await self._session.execute(
            select(DataRequest).where(DataRequest.id == request_id)
        )
        request = request.scalar_one_or_none()
        if not request:
            raise DataRequestNotFoundError(f"Data request with id {request_id} not found")
        return request

    async def update_request(
        self,
        request_id: int,
        request_data: Dict
    ) -> DataRequest:
        """Update a data request."""
        request = await self.get_request(request_id)
        for key, value in request_data.items():
            if hasattr(request, key):
                setattr(request, key, value)
        if "status" in request_data and request_data["status"] in ["completed", "failed"]:
            request.completed_at = datetime.utcnow()
        await self._session.commit()
        await self._session.refresh(request)
        return request

    async def get_user_requests(
        self,
        user_id: int,
        request_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[DataRequest]:
        """Get all data requests for a user."""
        query = select(DataRequest).where(DataRequest.user_id == user_id)
        if request_type:
            query = query.where(DataRequest.type == request_type)
        if status:
            query = query.where(DataRequest.status == status)
        query = query.order_by(desc(DataRequest.created_at))
        requests = await self._session.execute(query)
        return requests.scalars().all()

    async def create_archive(self, archive_data: Dict) -> DataArchive:
        """Create a data archive entry."""
        archive = DataArchive(
            original_id=archive_data["original_id"],
            data_type=archive_data["data_type"],
            content=archive_data["content"],
            archived_at=datetime.utcnow()
        )
        self._session.add(archive)
        await self._session.commit()
        await self._session.refresh(archive)
        return archive

    async def get_archive(self, archive_id: int) -> DataArchive:
        """Get a specific data archive."""
        archive = await self._session.execute(
            select(DataArchive).where(DataArchive.id == archive_id)
        )
        return archive.scalar_one_or_none()

    async def get_privacy_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get privacy-related statistics."""
        query = select(DataRequest)
        if start_date:
            query = query.where(DataRequest.created_at >= start_date)
        if end_date:
            query = query.where(DataRequest.created_at <= end_date)

        requests = await self._session.execute(query)
        requests = requests.scalars().all()

        # Calculate statistics
        total_requests = len(requests)
        export_requests = sum(1 for r in requests if r.type == "export")
        deletion_requests = sum(1 for r in requests if r.type == "deletion")
        completed_requests = sum(1 for r in requests if r.status == "completed")

        # Calculate average completion time for completed requests
        completion_times = [
            (r.completed_at - r.created_at).total_seconds()
            for r in requests
            if r.status == "completed" and r.completed_at
        ]
        avg_completion_time = (
            sum(completion_times) / len(completion_times)
            if completion_times else 0
        )

        return {
            "total_requests": total_requests,
            "export_requests": export_requests,
            "deletion_requests": deletion_requests,
            "completed_requests": completed_requests,
            "avg_completion_time": avg_completion_time,
            # These would be populated from other repositories
            "opted_out_users": 0,
            "marketing_consents": 0,
            "archived_items": 0,
            "deleted_items": 0
        }

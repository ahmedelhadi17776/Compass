from datetime import datetime
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc

from Backend.data.database.models import AuthLog
from .base_repository import BaseRepository

class AuthLogRepository(BaseRepository[AuthLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(AuthLog, session)

    async def get_by_user_id(self, user_id: int) -> List[AuthLog]:
        """Get all authentication logs for a specific user."""
        stmt = select(AuthLog).where(AuthLog.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_failed_attempts(self, user_id: int, since: datetime) -> List[AuthLog]:
        """Get failed login attempts for a user since a specific time."""
        stmt = select(AuthLog).where(
            AuthLog.user_id == user_id,
            AuthLog.status == "failure",
            AuthLog.created_at >= since
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ip_address(self, ip_address: str) -> List[AuthLog]:
        """Get all authentication logs from a specific IP address."""
        stmt = select(AuthLog).where(AuthLog.ip_address == ip_address)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

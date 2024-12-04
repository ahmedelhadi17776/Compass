from datetime import datetime
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc

from src.data.database.models import AuthenticationLog
from .base_repository import BaseRepository

class AuthLogRepository(BaseRepository[AuthenticationLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(AuthenticationLog, session)

    async def get_by_user_id(self, user_id: int) -> List[AuthenticationLog]:
        """Get all authentication logs for a specific user."""
        stmt = select(AuthenticationLog).where(AuthenticationLog.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_failed_attempts(self, user_id: int, since: datetime) -> List[AuthenticationLog]:
        """Get failed login attempts for a user since a specific time."""
        stmt = select(AuthenticationLog).where(
            AuthenticationLog.user_id == user_id,
            AuthenticationLog.login_status == "failed",
            AuthenticationLog.timestamp >= since
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ip_address(self, ip_address: str) -> List[AuthenticationLog]:
        """Get all authentication logs from a specific IP address."""
        stmt = select(AuthenticationLog).where(AuthenticationLog.ip_address == ip_address)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

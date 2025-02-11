from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.utils.datetime_utils import utc_now

from Backend.domain.models.session import Session
from .base_repository import BaseRepository

class SessionRepository(BaseRepository[Session]):
    def __init__(self, session: AsyncSession):
        super().__init__(Session, session)

    async def get_by_auth_token(self, auth_token: str) -> Optional[Session]:
        """Get a session by its auth token."""
        stmt = select(Session).where(Session.auth_token == auth_token)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_user_id(self, user_id: int) -> List[Session]:
        """Get all active sessions for a specific user."""
        now = utc_now()
        stmt = select(Session).where(
            Session.user_id == user_id,
            Session.expires_at > now
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_expired(self) -> int:
        """Delete all expired sessions."""
        now = utc_now()
        stmt = select(Session).where(Session.expires_at <= now)
        result = await self.session.execute(stmt)
        expired_sessions = result.scalars().all()
        
        count = 0
        for session in expired_sessions:
            await self.session.delete(session)
            count += 1
        
        if count > 0:
            await self.session.commit()
        
        return count

"""Session management module."""
from datetime import datetime, timedelta
import secrets
from typing import Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.core.config import settings
from src.data.database.models import UserSession
from src.utils.datetime_utils import utc_now
from .exceptions import InvalidSessionError

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: int) -> UserSession:
        """Create a new session for user."""
        # Check existing sessions count
        existing_sessions = await self.db.execute(
            select(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
        )
        if len(existing_sessions.scalars().all()) >= settings.MAX_SESSIONS_PER_USER:
            # Deactivate oldest session
            oldest_session = await self.db.execute(
                select(UserSession)
                .filter(UserSession.user_id == user_id)
                .order_by(UserSession.created_at)
                .limit(1)
            )
            if oldest := oldest_session.scalar_one_or_none():
                oldest.is_active = False

        # Create new session
        session = UserSession(
            user_id=user_id,
            session_token=secrets.token_urlsafe(32),
            expires_at=utc_now() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES),
            is_active=True
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def validate_session(self, session_token: str) -> UserSession:
        """Validate and refresh session if needed."""
        session = await self.db.execute(
            select(UserSession).filter(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > utc_now()
                )
            )
        )
        session = session.scalar_one_or_none()

        if not session:
            raise InvalidSessionError()

        # Check if session needs refresh
        if (utc_now() - session.last_activity).total_seconds() < (
            settings.SESSION_REFRESH_MINUTES * 60
        ):
            session.expires_at = utc_now() + timedelta(
                minutes=settings.SESSION_EXPIRE_MINUTES
            )
            session.last_activity = utc_now()
            await self.db.commit()

        return session

    async def end_session(self, session_token: str) -> bool:
        """End a specific session."""
        session = await self.db.execute(
            select(UserSession).filter(
                UserSession.session_token == session_token)
        )
        if session := session.scalar_one_or_none():
            session.is_active = False
            session.ended_at = utc_now()
            await self.db.commit()
            return True
        return False

    async def cleanup_expired_sessions(self):
        """Cleanup expired sessions."""
        try:
            result = await self.db.execute(
                select(UserSession).filter(
                    and_(
                        UserSession.is_active == True,
                        UserSession.expires_at <= utc_now()
                    )
                )
            )
            expired_sessions = result.scalars().all()

            for session in expired_sessions:
                session.is_active = False
                session.ended_at = utc_now()

            await self.db.commit()
            if expired_sessions:
                logger.info(
                    f"Cleaned up {len(expired_sessions)} expired sessions")
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")

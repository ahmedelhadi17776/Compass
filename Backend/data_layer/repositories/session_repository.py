from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from Backend.data_layer.database.models.session import Session
import json


class SessionRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_session(self, user_id: int, token: str, expires_at: datetime, device_info: str = None, ip_address: str = None) -> Session:
        # Convert device_info string to a dictionary
        device_info_dict = {"user_agent": device_info} if device_info else None

        session = Session(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            device_info=device_info_dict,
            ip_address=ip_address
        )
        self.db_session.add(session)
        await self.db_session.commit()
        await self.db_session.refresh(session)
        return session

    async def get_valid_session(self, token: str) -> Session | None:
        query = select(Session).where(
            and_(
                Session.token == token,
                Session.is_valid == True,
                Session.expires_at > datetime.utcnow()
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def invalidate_session(self, token: str) -> bool:
        stmt = update(Session).where(
            Session.token == token).values(is_valid=False)
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount > 0

    async def get_user_sessions(self, user_id: int) -> list[Session]:
        query = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.is_valid == True,
                Session.expires_at > datetime.utcnow()
            )
        )
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def cleanup_expired_sessions(self) -> int:
        stmt = update(Session).where(
            and_(
                Session.is_valid == True,
                Session.expires_at <= datetime.utcnow()
            )
        ).values(is_valid=False)
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        return result.rowcount

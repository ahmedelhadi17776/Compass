from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from Backend.data_layer.database.models.user import User


class UserRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_username(self, username: str):
        query = select(User).where(User.username == username)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int):
        query = select(User).where(User.id == user_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, **user_data):
        user = User(**user_data)
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

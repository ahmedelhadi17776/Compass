from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from Backend.data_layer.database.models.user import User
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status


class UserRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_username(self, username: str):
        try:
            query = select(User).where(User.username == username)
            result = await self.db_session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

    async def get_by_id(self, user_id: int):
        try:
            query = select(User).where(User.id == user_id)
            result = await self.db_session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

    async def create(self, **user_data):
        try:
            user = User(**user_data)
            self.db_session.add(user)
            await self.db_session.commit()
            await self.db_session.refresh(user)
            return user
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, update
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

    async def get_by_email(self, email: str):
        query = select(User).where(User.email == email)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, user_id: int, update_data: dict) -> User:
        """Update user with given data"""
        try:
            # First update the user
            query = update(User).where(User.id == user_id).values(**update_data)
            await self.db_session.execute(query)
            
            # Then fetch and return the updated user
            await self.db_session.commit()
            
            # Get the updated user
            updated_user = await self.get_by_id(user_id)
            return updated_user
            
        except Exception as e:
            await self.db_session.rollback()
            raise e

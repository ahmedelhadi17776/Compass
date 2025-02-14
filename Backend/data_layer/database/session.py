from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from data_layer.database.connection import async_session

# ✅ Helper function to get a single database session


from typing import AsyncGenerator

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

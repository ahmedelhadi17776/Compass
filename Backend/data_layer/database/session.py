from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from Backend.data_layer.database.connection import async_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    session = async_session()
    try:
        yield session
    finally:
        await session.close()

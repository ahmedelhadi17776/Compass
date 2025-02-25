from sqlalchemy.ext.asyncio import AsyncSession
from Backend.data_layer.database.connection import async_session


async def get_db_session() -> AsyncSession:
    return async_session()  # Return the async session directly

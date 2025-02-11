import asyncio
from Backend.core.database import engine, Base
from Backend.core.logging import logger
from Backend.data.database.models import *  # Import all models


async def init_db():
    """Initialize the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())

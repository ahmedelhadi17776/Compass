from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from Backend.core.config import settings

# ✅ Create Async Database Engine
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

# ✅ Create Session Factory
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)

# ✅ Dependency Injection for DB


async def get_db():
    async with async_session() as session:
        yield session

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# ✅ Create Async Engine
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

# ✅ Create Async Session Factory
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)

# ✅ Get DB Session Dependency


async def get_db():
    async with async_session() as session:
        yield session

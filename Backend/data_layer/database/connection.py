from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from Backend.core.config import settings
from sqlalchemy import text, event
from sqlalchemy.engine import Engine

# Create async engine based on settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,  # Enable connection health checks
    isolation_level="READ COMMITTED",  # Explicit isolation level
    pool_size=5,
    max_overflow=10,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False  # Ensure explicit transaction management
)

# Get DB Session Dependency


async def get_db():
    session = async_session()
    try:
        # Set search path to public schema
        await session.execute(text("SET search_path TO public"))

        # Test the connection
        await session.execute(text("SELECT 1"))

        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise
    finally:
        await session.close()

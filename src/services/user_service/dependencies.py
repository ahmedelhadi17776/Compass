"""User service dependencies."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import SecurityContext
from src.data.database.session import get_db
from src.services.authentication.dependencies import get_security_context
from .user_service import UserService


async def get_user_service(
    db: AsyncSession = Depends(get_db),
    security_context: SecurityContext = Depends(get_security_context)
) -> UserService:
    """Get user service instance."""
    return UserService(db, security_context)

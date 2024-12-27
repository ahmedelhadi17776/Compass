"""Security service dependencies."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import SecurityContext
from src.data.database.session import get_db
from src.services.authentication.dependencies import get_security_context
from .security_service import SecurityService


async def get_security_service(
    db: AsyncSession = Depends(get_db),
    security_context: SecurityContext = Depends(get_security_context)
) -> SecurityService:
    """Get security service instance."""
    return SecurityService(db, security_context)

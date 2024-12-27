"""Authentication dependencies."""
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import SecurityContext
from src.data.database.session import get_db
from .auth_service import AuthService


async def get_security_context(request: Request) -> SecurityContext:
    """Get security context from request state."""
    return request.state.security_context


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
    security_context: SecurityContext = Depends(get_security_context)
) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db, security_context)

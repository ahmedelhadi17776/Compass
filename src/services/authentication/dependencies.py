"""Authentication dependencies."""
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from jose import JWTError

from src.core.security import SecurityContext
from src.data.database.session import get_db
from .auth_service import AuthService
from src.core.security.jwt_utils import decode_access_token
from src.data.database.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_security_context(request: Request) -> SecurityContext:
    """Get security context from request state."""
    return request.state.security_context


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
    security_context: SecurityContext = Depends(get_security_context)
) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db, security_context)


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Retrieve the current user based on JWT token."""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

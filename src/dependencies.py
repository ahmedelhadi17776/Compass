"""Application dependencies."""
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from .data.database.connection import get_db
from .data.database.models import User
from .core.config import settings
from .application.schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_db_session() -> Generator[Session, None, None]:
    """Get database session."""
    db = get_db()
    try:
        yield next(db)
    finally:
        pass

def get_auth_service():
    """Get AuthService instance."""
    # Import here to avoid circular imports
    from .services.authentication.auth_service import AuthService
    db = next(get_db_session())
    return AuthService(db)

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get current authenticated user."""
    auth_service = get_auth_service()
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(user_id=int(user_id))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_service.get_user_by_id(token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    return user

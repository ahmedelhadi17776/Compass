from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from src.data.database.connection import get_db
from src.data.database.models import User
from src.services.authentication.jwt_handler import verify_token
from .dependencies import get_auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    if username is None or user_id is None:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.UserID == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_auth_service(db: Session = Depends(get_db)) -> Generator[AuthService, None, None]:
    """Get AuthService instance."""
    service = AuthService(db)
    try:
        yield service
    finally:
        pass

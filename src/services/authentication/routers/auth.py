from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.application.schemas.auth import UserCreate, UserLogin, Token
from src.services.authentication.auth_service import AuthService
from src.data.database.connection import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    auth_service = AuthService(db)
    try:
        token = await auth_service.register_user(user)
        return token
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return token."""
    auth_service = AuthService(db)
    token = await auth_service.authenticate_user(credentials)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return token

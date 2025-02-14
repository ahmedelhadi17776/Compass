from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from utils.security_utils import hash_password, verify_password, create_access_token, decode_access_token
from data_layer.database.connection import get_db
from data_layer.database.models.user import User

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


# ✅ Register User (Now Supports Async)
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(email: str, username: str, password: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"message": "User registered successfully"}


@router.post("/token")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(
        (User.email.ilike(form_data.username)) | (
            User.username.ilike(form_data.username))
    ))
    user = result.scalars().first()

    print(f"🔍 Querying for user: {form_data.username}")
    print(f"🛠️ Found User: {user}")

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=60))

    print(f"✅ Generated JWT Token: {access_token}")  # Debugging

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    print(f"🔍 Received Token in /auth/me: {token}")  # Debugging

    payload = decode_access_token(token)
    if not payload:
        print("🔴 Token is invalid or expired!")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = payload.get("sub")

    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()

    if not user:
        print("🔴 User not found in database!")
        raise HTTPException(status_code=404, detail="User not found")

    print(f"✅ User Found: {user.username}")
    return {"email": user.email, "username": user.username, "is_active": user.is_active}

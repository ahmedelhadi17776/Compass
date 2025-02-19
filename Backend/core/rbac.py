from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from Backend.utils.security_utils import decode_access_token
from Backend.data_layer.database.connection import get_db
from Backend.data_layer.database.models.user import User, Role, UserRole
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


# ✅ Get Current User from JWT Token
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email = payload.get("sub")
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


async def has_role(user, role_name, db):
    result = await db.execute(select(UserRole).join(Role).filter(
        UserRole.user_id == user.id,
        Role.name == role_name
    ))
    user_roles = result.scalars().all()

    return len(user_roles) > 0


# ✅ Require Role for Route Access
def require_role(role_name: str):
    def role_checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        if not has_role(user, role_name, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires role: {role_name}"
            )
        return user
    return role_checker

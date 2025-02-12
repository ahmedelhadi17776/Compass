from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.rbac import get_current_user, require_role
from data_layer.database.connection import get_db
from data_layer.database.models.user import User, Role, UserRole

router = APIRouter()


# ✅ Create a New Role (Admin Only)
@router.post("/roles/", status_code=status.HTTP_201_CREATED)
async def create_role(name: str, description: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin"))):
    result = await db.execute(select(Role).filter(Role.name == name))
    existing_role = result.scalars().first()

    if existing_role:
        raise HTTPException(status_code=400, detail="Role already exists")

    new_role = Role(name=name, description=description)
    db.add(new_role)
    await db.commit()
    await db.refresh(new_role)
    return {"message": "Role created successfully"}


# ✅ Assign Role to User (Admin Only)
@router.post("/users/{user_id}/assign-role/")
async def assign_role(user_id: int, role_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin"))):
    user_role = UserRole(user_id=user_id, role_id=role_id)
    db.add(user_role)
    await db.commit()
    return {"message": "Role assigned successfully"}


# ✅ Get User's Roles (Authenticated User)
@router.get("/users/me/roles")
async def get_my_roles(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserRole).filter(UserRole.user_id == user.id))
    user_roles = result.scalars().all()

    role_ids = [ur.role_id for ur in user_roles]

    result = await db.execute(select(Role).filter(Role.id.in_(role_ids)))
    roles = result.scalars().all()

    return {"roles": [role.name for role in roles]}

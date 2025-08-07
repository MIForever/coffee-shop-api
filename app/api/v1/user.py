from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.deps import get_db
from app.models import User, UserRole
from app.schemas.user import UserRead, UserUpdate, UserRoleUpdate
from app.core.auth import get_current_user, require_admin
from app.core.security import get_password_hash
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me",
    summary="Get current user",
    description="Returns the currently authenticated user's profile information.",
    response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/",
    summary="List all users",
    description="Returns a list of all users. Accessible only by admin users.",
    response_model=List[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    result = await db.execute(select(User))
    return result.scalars().all()

@router.get("/{user_id}",
    summary="Get user by ID",
    description="Returns a user's profile information by ID. Accessible only by admin users.",
    response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}",
    summary="Update user by ID",
    description="Allows users to update their own data and admins to update anyone.",
    response_model=UserRead)
async def update_user(
    user_id: int,
    updates: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Restrict non-admins to updating only their own data
    if current_user.role.value != "ADMIN" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to update this user")

    update_data = updates.model_dump(exclude_unset=True)
    
    # Handle password hashing separately
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}",
    summary="Delete user",
    description="Deletes a user by ID. Only accessible by admins.",
    response_model=dict)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted"}

@router.patch("/{user_id}/role",
    summary="Change user role",
    description="Changes a user's role. Only accessible by admins.",
    response_model=UserRead)
async def change_user_role(
    user_id: int,
    new_role: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role_value = new_role.role
    if role_value not in UserRole.__members__:
        raise HTTPException(status_code=400, detail="Invalid role")

    user.role = role_value
    await db.commit()
    await db.refresh(user)
    return user
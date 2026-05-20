"""
User management API for administrators.
"""
from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, EmailStr

from ..models.user import User, UserRole, UserRoleAssignment, Gender
from ..services.auth_service import AuthService
from ..services.authorization_service import AuthorizationService
from ..core.database import get_db
from ..core.redis import cache_manager, session_manager
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/users", tags=["users"])


# ──────────────────────────── Schemas ─────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: Optional[str] = None
    gender: Optional[str] = "OTHER"
    role: str = Field(..., description="STUDENT, LECTURER, EXAM_OFFICER, INVIGILATOR, ADMINISTRATOR, SUPER_ADMIN")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    is_active: Optional[bool] = None


class RoleAssign(BaseModel):
    role: str = Field(..., description="Role to assign")
    department_id: Optional[str] = None
    expires_at: Optional[datetime] = None


class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone_number: Optional[str]
    gender: Optional[str]
    is_verified: bool
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: Optional[datetime]
    roles: List[str]


# ──────────────────────────── Users CRUD ────────────────────────────────────

@router.get("/", dependencies=[Depends(require_permission("user.read"))])
async def list_users(
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search username, email, or name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> List[dict]:
    """List all users with optional filters."""
    query = {}
    
    if is_active is not None:
        query["is_active"] = is_active
    
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
        ]
    
    users = await User.find(query).sort("-created_at").skip(offset).limit(limit).to_list()
    
    # Get roles for each user
    authz = AuthorizationService(cache_manager)
    result = []
    for user in users:
        user_roles = await authz.get_user_roles(str(user.id))
        
        # Filter by role if specified
        if role and role.upper() not in user_roles:
            continue
            
        result.append({
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "gender": user.gender.value if user.gender else None,
            "is_verified": user.is_verified,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "roles": user_roles,
        })
    
    return result


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("user.create"))])
async def create_user(
    data: UserCreate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    """Create a new user with role."""
    auth_service = AuthService(db, cache_manager, session_manager)
    
    # Validate role
    try:
        user_role = UserRole(data.role.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{data.role}'. Must be one of: {', '.join([r.value for r in UserRole])}"
        )
    
    # Convert gender string to enum
    gender_enum = None
    if data.gender:
        try:
            gender_enum = Gender(data.gender.upper())
        except ValueError:
            gender_enum = Gender.OTHER
    
    # Create user
    try:
        user = await auth_service.register_user(
            username=data.username,
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
            date_of_birth=None,
            gender=gender_enum,
            ip_address="127.0.0.1",
            user_agent="admin-created"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    
    # Verify user
    await user.set({User.is_verified: True})
    
    # Assign role
    role_assignment = UserRoleAssignment(
        user_id=str(user.id),
        role=user_role,
        granted_by=str(current_user.id)
    )
    await role_assignment.insert()
    
    # Clear cache
    authz = AuthorizationService(cache_manager)
    await authz.invalidate_user_cache(str(user.id))
    
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user_role.value,
        "message": "User created successfully"
    }


@router.get("/{user_id}", dependencies=[Depends(require_permission("user.read"))])
async def get_user(
    user_id: str,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    """Get user details."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    authz = AuthorizationService(cache_manager)
    roles = await authz.get_user_roles(user_id)
    
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "gender": user.gender.value if user.gender else None,
        "is_verified": user.is_verified,
        "is_active": user.is_active,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
        "roles": roles,
    }


@router.patch("/{user_id}", dependencies=[Depends(require_permission("user.update"))])
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    """Update user details."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    updates = data.model_dump(exclude_unset=True)
    if updates:
        await user.set(updates)
    
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "message": "User updated successfully"
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("user.delete"))])
async def delete_user(
    user_id: str,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
):
    """Delete user and their role assignments."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Don't allow self-deletion
    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    
    # Delete role assignments
    await UserRoleAssignment.find({"user_id": user_id}).delete()
    
    # Clear cache
    authz = AuthorizationService(cache_manager)
    await authz.invalidate_user_cache(user_id)
    
    # Delete user
    await user.delete()


# ──────────────────────────── Role Management ───────────────────────────────

@router.post("/{user_id}/roles", dependencies=[Depends(require_permission("user.update"))])
async def assign_role(
    user_id: str,
    data: RoleAssign,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    """Assign a role to user."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Validate role
    try:
        user_role = UserRole(data.role.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{data.role}'"
        )
    
    # Check if role already exists
    existing = await UserRoleAssignment.find_one({
        "user_id": user_id,
        "role": user_role
    })
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already assigned")
    
    # Create assignment
    assignment = UserRoleAssignment(
        user_id=user_id,
        role=user_role,
        department_id=data.department_id,
        granted_by=str(current_user.id),
        expires_at=data.expires_at
    )
    await assignment.insert()
    
    # Clear cache
    authz = AuthorizationService(cache_manager)
    await authz.invalidate_user_cache(user_id)
    
    return {"message": f"Role {user_role.value} assigned successfully"}


@router.delete("/{user_id}/roles/{role}", dependencies=[Depends(require_permission("user.update"))])
async def remove_role(
    user_id: str,
    role: str,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
):
    """Remove a role from user."""
    try:
        user_role = UserRole(role.upper())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role '{role}'")
    
    assignment = await UserRoleAssignment.find_one({
        "user_id": user_id,
        "role": user_role
    })
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role assignment not found")
    
    await assignment.delete()
    
    # Clear cache
    authz = AuthorizationService(cache_manager)
    await authz.invalidate_user_cache(user_id)
    
    return {"message": f"Role {user_role.value} removed successfully"}


# ──────────────────────────── Password Reset ────────────────────────────────

@router.post("/{user_id}/reset-password", dependencies=[Depends(require_permission("user.update"))])
async def reset_password(
    user_id: str,
    data: PasswordReset,
    current_user=Depends(get_current_active_user),
    db: Any = Depends(get_db),
) -> dict:
    """Reset user password (admin only)."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    auth_service = AuthService(db, cache_manager, session_manager)
    salt = auth_service.security.generate_salt()
    password_hash = auth_service.security.hash_password(data.new_password, salt)
    
    await user.set({
        User.salt: salt,
        User.password_hash: password_hash
    })
    
    # Invalidate sessions to force re-login
    await session_manager.clear_user_sessions(user_id)
    
    return {"message": "Password reset successfully. User must log in again."}


@router.post("/me/clear-cache")
async def clear_my_cache(
    current_user=Depends(get_current_active_user),
) -> dict:
    """Clear permission cache for current user (force refresh)."""
    authz = AuthorizationService(cache_manager)
    await authz.invalidate_user_cache(str(current_user.id))
    return {"message": "Cache cleared. Permissions will be refreshed on next request."}

"""
User management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from database import get_db
from models import User, Role
from schemas import UserResponse, UserCreate, UserUpdate, UserProfileUpdate, RoleResponse
from auth import get_current_active_user, get_password_hash, check_role_permission

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all users"""
    check_role_permission(current_user, ["Admin", "Management"])
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update current user's own profile (email, full_name, badge_id, password)"""
    update_data = profile_update.model_dump(exclude_unset=True)
    
    # Handle password update
    if "password" in update_data:
        if not update_data["password"]:
            # Remove password from update if empty
            update_data.pop("password")
        else:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    # Convert empty strings to None for optional fields to avoid unique constraint issues
    # This ensures NULL values in database instead of empty strings, which is important for UNIQUE constraints
    # PostgreSQL allows multiple NULL values in UNIQUE columns, but not multiple empty strings
    if "email" in update_data:
        email_value = update_data["email"]
        if email_value and isinstance(email_value, str):
            email_value = email_value.strip()
        update_data["email"] = email_value if email_value else None
    if "full_name" in update_data:
        full_name_value = update_data["full_name"]
        if full_name_value and isinstance(full_name_value, str):
            full_name_value = full_name_value.strip()
        update_data["full_name"] = full_name_value if full_name_value else None
    if "badge_id" in update_data:
        badge_id_value = update_data["badge_id"]
        if badge_id_value and isinstance(badge_id_value, str):
            badge_id_value = badge_id_value.strip()
        update_data["badge_id"] = badge_id_value if badge_id_value else None
    
    # Check if email is being updated and if it's already taken by another user
    if "email" in update_data and update_data["email"]:
        existing_user = db.query(User).filter(
            User.email == update_data["email"],
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered to another user"
            )
    
    # Check if badge_id is being updated and if it's already taken by another user
    if "badge_id" in update_data and update_data["badge_id"]:
        existing_user = db.query(User).filter(
            User.badge_id == update_data["badge_id"],
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Badge ID already registered to another user"
            )
    
    # Update only allowed fields
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except IntegrityError as e:
        db.rollback()
        # Handle database constraint violations (unique constraints, foreign keys, etc.)
        error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()
        if "unique" in error_msg or "duplicate" in error_msg:
            if "email" in error_msg:
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered to another user"
                )
            elif "badge_id" in error_msg or "badge" in error_msg:
                raise HTTPException(
                    status_code=400,
                    detail="Badge ID already registered to another user"
                )
        # Generic integrity error
        raise HTTPException(
            status_code=400,
            detail="Database constraint violation. Please check your input."
        )
    except Exception as e:
        db.rollback()
        # Log unexpected errors for debugging
        print(f"Unexpected error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update profile. Please try again."
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a user"""
    check_role_permission(current_user, ["Admin", "Management"])
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle password update
    if "password" in update_data:
        if not update_data["password"]:
            # Remove password from update if empty
            update_data.pop("password")
        else:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    # Convert empty strings to None for optional fields to avoid unique constraint issues
    # PostgreSQL allows multiple NULL values in UNIQUE columns, but not multiple empty strings
    if "email" in update_data:
        email_value = update_data["email"]
        if email_value and isinstance(email_value, str):
            email_value = email_value.strip()
        update_data["email"] = email_value if email_value else None
    if "full_name" in update_data:
        full_name_value = update_data["full_name"]
        if full_name_value and isinstance(full_name_value, str):
            full_name_value = full_name_value.strip()
        update_data["full_name"] = full_name_value if full_name_value else None
    if "badge_id" in update_data:
        badge_id_value = update_data["badge_id"]
        if badge_id_value and isinstance(badge_id_value, str):
            badge_id_value = badge_id_value.strip()
        update_data["badge_id"] = badge_id_value if badge_id_value else None
    
    # Check if email is being updated and if it's already taken by another user
    if "email" in update_data and update_data["email"]:
        existing_user = db.query(User).filter(
            User.email == update_data["email"],
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered to another user"
            )
    
    # Check if badge_id is being updated and if it's already taken by another user
    if "badge_id" in update_data and update_data["badge_id"]:
        existing_user = db.query(User).filter(
            User.badge_id == update_data["badge_id"],
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Badge ID already registered to another user"
            )
    
    # Update only allowed fields
    for field, value in update_data.items():
        setattr(user, field, value)
    
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError as e:
        db.rollback()
        # Handle database constraint violations (unique constraints, foreign keys, etc.)
        error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()
        if "unique" in error_msg or "duplicate" in error_msg:
            if "email" in error_msg:
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered to another user"
                )
            elif "badge_id" in error_msg or "badge" in error_msg:
                raise HTTPException(
                    status_code=400,
                    detail="Badge ID already registered to another user"
                )
        # Generic integrity error
        raise HTTPException(
            status_code=400,
            detail="Database constraint violation. Please check your input."
        )
    except Exception as e:
        db.rollback()
        # Log unexpected errors for debugging
        print(f"Unexpected error updating user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update user. Please try again."
        )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a user"""
    check_role_permission(current_user, ["Admin"])
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.get("/roles/", response_model=List[RoleResponse])
async def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all roles"""
    roles = db.query(Role).all()
    return roles

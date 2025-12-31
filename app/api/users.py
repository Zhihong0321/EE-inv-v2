from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.repositories.user_repo import UserRepository
from app.middleware.auth import get_current_user
from app.models.auth import AuthUser

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("", response_model=dict)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("registration_date", description="Sort by: name, email, registration_date, whatsapp_number"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users with their agent profiles, sorted by specified column"""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access user management"
        )
    
    # Validate sort_order
    if sort_order.lower() not in ["asc", "desc"]:
        sort_order = "desc"
    
    user_repo = UserRepository(db)
    users, total = user_repo.get_all(
        skip=skip, 
        limit=limit, 
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit,
        "sort_by": sort_by,
        "sort_order": sort_order
    }


@router.get("/{user_bubble_id}", response_model=UserResponse)
def get_user(
    user_bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by bubble_id"""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access user management"
        )
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_bubble_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user with agent profile"""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create users"
        )
    
    user_repo = UserRepository(db)
    user = user_repo.create_user(
        name=user_data.name,
        whatsapp_number=user_data.whatsapp_number,
        email=user_data.email,
        linked_agent_profile=user_data.linked_agent_profile,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    return UserResponse(**user)


@router.put("/{user_bubble_id}", response_model=UserResponse)
def update_user(
    user_bubble_id: str,
    user_data: UserUpdate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user and/or agent profile"""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update users"
        )
    
    user_repo = UserRepository(db)
    user = user_repo.update_user(
        user_bubble_id=user_bubble_id,
        name=user_data.name,
        whatsapp_number=user_data.whatsapp_number,
        email=user_data.email,
        linked_agent_profile=user_data.linked_agent_profile,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user)


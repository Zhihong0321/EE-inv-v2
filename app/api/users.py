from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.schemas.user import (
    UserResponse, UserCreate, UserUpdate, UserTagsUpdate,
    TagRegistryResponse, TagRegistryCreate
)
from app.repositories.user_repo import UserRepository
from app.repositories.tag_registry_repo import TagRegistryRepository
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.tag_registry import TagCategory

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("", response_model=dict)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("registration_date", description="Sort by: name, email, registration_date, whatsapp_number"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    
    # If access_level is provided, validate tags first
    if user_data.access_level is not None:
        tag_repo = TagRegistryRepository(db)
        valid_tags, invalid_tags = tag_repo.validate_tags(user_data.access_level)
        if invalid_tags:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tags: {', '.join(invalid_tags)}"
            )
        # Use only valid tags
        user_data.access_level = valid_tags
    
    user = user_repo.update_user(
        user_bubble_id=user_bubble_id,
        name=user_data.name,
        whatsapp_number=user_data.whatsapp_number,
        email=user_data.email,
        linked_agent_profile=user_data.linked_agent_profile,
        access_level=user_data.access_level,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user)


@router.put("/{user_bubble_id}/tags", response_model=UserResponse)
def update_user_tags(
    user_bubble_id: str,
    tags_data: UserTagsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user tags only"""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update user tags"
        )
    
    # Validate tags against registry
    tag_repo = TagRegistryRepository(db)
    valid_tags, invalid_tags = tag_repo.validate_tags(tags_data.tags)
    
    if invalid_tags:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tags: {', '.join(invalid_tags)}. Valid tags must exist in tag registry."
        )
    
    user_repo = UserRepository(db)
    user = user_repo.update_user_tags(
        user_bubble_id=user_bubble_id,
        tags=valid_tags
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user)


# Tag Registry Endpoints
@router.get("/tags/registry", response_model=dict)
def get_tag_registry(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tags from registry grouped by category"""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access tag registry"
        )
    
    tag_repo = TagRegistryRepository(db)
    tags_by_category = tag_repo.get_all_tags()
    
    return {
        "tags": tags_by_category,
        "total": sum(len(tags) for tags in tags_by_category.values())
    }


@router.post("/tags/registry", response_model=TagRegistryResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagRegistryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new tag in registry"""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create tags"
        )
    
    # Validate category
    try:
        category = TagCategory(tag_data.category.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: app, function, department"
        )
    
    tag_repo = TagRegistryRepository(db)
    
    # Check if tag already exists
    existing_tag = tag_repo.get_tag(tag_data.tag)
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag '{tag_data.tag}' already exists"
        )
    
    tag_registry = tag_repo.create_tag(
        tag=tag_data.tag,
        category=category,
        description=tag_data.description
    )
    
    return TagRegistryResponse(
        tag=tag_registry.tag,
        category=tag_registry.category.value,
        description=tag_registry.description
    )


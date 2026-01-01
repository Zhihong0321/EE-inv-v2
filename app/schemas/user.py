from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserResponse(BaseModel):
    """User response schema"""
    user_bubble_id: str = Field(..., alias="user_bubble_id")
    agent_bubble_id: Optional[str] = None
    name: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    registration_date: Optional[datetime] = None
    linked_agent_profile: Optional[str] = None
    access_level: Optional[List[str]] = []  # Tags/permissions
    
    class Config:
        populate_by_name = True
        from_attributes = True


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    name: str
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    linked_agent_profile: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    name: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    linked_agent_profile: Optional[str] = None
    access_level: Optional[List[str]] = None  # Tags/permissions


class UserTagsUpdate(BaseModel):
    """Schema for updating user tags only"""
    tags: List[str]  # List of tag strings


class TagRegistryResponse(BaseModel):
    """Tag registry response schema"""
    tag: str
    category: str
    description: Optional[str] = None


class TagRegistryCreate(BaseModel):
    """Schema for creating a tag in registry"""
    tag: str
    category: str  # "app", "function", or "department"
    description: Optional[str] = None



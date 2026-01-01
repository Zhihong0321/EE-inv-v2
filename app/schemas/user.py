from pydantic import BaseModel, Field
from typing import Optional
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



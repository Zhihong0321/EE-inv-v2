from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SendOTPRequest(BaseModel):
    whatsapp_number: str = Field(..., description="WhatsApp number with country code (digits only)")


class VerifyOTPRequest(BaseModel):
    whatsapp_number: str
    otp_code: str = Field(..., pattern=r"^\d{6}$", description="6-digit OTP code")
    name: Optional[str] = None


class VerifyOTPResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    user_id: str
    whatsapp_number: str
    name: Optional[str] = None
    role: str
    active: bool
    app_permissions: List[str] = []
    created_at: datetime
    last_login_at: Optional[datetime] = None


class APIKeyCreate(BaseModel):
    service_name: str
    app_domain: str
    permissions: List[str]
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    api_key_id: str
    service_name: str
    app_domain: str
    permissions: List[str]
    active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    api_key_secret: Optional[str] = None  # Only shown on creation


class APIKeyCreateResponse(BaseModel):
    success: bool
    api_key_id: str
    api_key_secret: str  # Only shown once
    message: str

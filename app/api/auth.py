from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.schemas.auth import (
    SendOTPRequest, VerifyOTPRequest, VerifyOTPResponse,
    LoginResponse, UserResponse, APIKeyCreate, APIKeyResponse, APIKeyCreateResponse
)
from app.repositories.auth_repo import AuthRepository
from app.utils.security import generate_otp, create_access_token
from app.middleware.auth import get_current_user, get_api_key_user, get_request_ip
from app.models.user import User
from app.services.whatsapp_service import whatsapp_service
from app.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/whatsapp/send-otp", response_model=dict)
async def send_otp(
    request: SendOTPRequest,
    db: Session = Depends(get_db)
):
    """Send OTP to WhatsApp number"""
    # Check WhatsApp service status
    status_result = await whatsapp_service.check_status()
    if not status_result.get("ready"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WhatsApp service not ready"
        )

    # Get or create user
    auth_repo = AuthRepository(db)
    user = auth_repo.get_or_create_user_by_whatsapp(request.whatsapp_number)

    # Generate and set OTP
    otp_code = generate_otp()
    auth_repo.set_user_otp(user.user_id, otp_code)

    # Send OTP via WhatsApp
    sent = await whatsapp_service.send_otp(
        phone=request.whatsapp_number,
        otp_code=otp_code,
        name=user.name
    )

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )

    return {
        "success": True,
        "message": "OTP sent to your WhatsApp",
        "expires_in": settings.OTP_EXPIRE_SECONDS
    }


@router.post("/whatsapp/verify", response_model=VerifyOTPResponse)
async def verify_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """Verify OTP and get JWT token"""
    auth_repo = AuthRepository(db)

    # Verify OTP
    user = auth_repo.verify_user_otp(request.whatsapp_number, request.otp_code)
    if not user:
        return VerifyOTPResponse(
            success=False,
            message="Invalid or expired OTP"
        )

    # Update name if provided
    if request.name and not user.name:
        user.name = request.name
        db.commit()

    # Create access token
    access_token = create_access_token(data={"sub": user.user_id})

    return VerifyOTPResponse(
        success=True,
        token=access_token,
        user={
            "user_id": user.user_id,
            "whatsapp_number": user.whatsapp_number,
            "name": user.name,
            "role": user.role,
            "active": user.active,
        },
        message="Login successful"
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse(
        user_id=current_user.user_id,
        whatsapp_number=current_user.whatsapp_number,
        name=current_user.name,
        role=current_user.role,
        active=current_user.active,
        app_permissions=current_user.app_permissions or [],
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
    )


@router.post("/logout")
def logout(
    request: Request
):
    """Logout user - redirect to Auth Hub logout"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="https://auth.atap.solar/auth/logout", status_code=302)


@router.post("/api-key/generate", response_model=APIKeyCreateResponse)
def generate_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key for microservice access"""
    auth_repo = AuthRepository(db)

    api_key, api_key_secret = auth_repo.create_api_key(
        created_by=current_user.id,
        service_name=api_key_data.service_name,
        app_domain=api_key_data.app_domain,
        permissions=api_key_data.permissions,
        expires_in_days=api_key_data.expires_in_days,
    )

    return APIKeyCreateResponse(
        success=True,
        api_key_id=api_key.key_id,
        api_key_secret=api_key_secret,
        message="API key generated successfully"
    )


@router.get("/api-keys", response_model=list[APIKeyResponse])
def get_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all API keys for current user"""
    auth_repo = AuthRepository(db)
    api_keys = auth_repo.get_api_keys(str(current_user.id))

    return [
        APIKeyResponse(
            api_key_id=key.key_id,
            service_name=key.service_name,
            app_domain=key.app_domain,
            permissions=key.permissions or [],
            active=key.active,
            expires_at=key.expires_at,
            created_at=key.created_at,
        )
        for key in api_keys
    ]


@router.delete("/api-keys/{key_id}")
def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an API key"""
    auth_repo = AuthRepository(db)
    success = auth_repo.revoke_api_key(key_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return {"message": "API key revoked successfully"}

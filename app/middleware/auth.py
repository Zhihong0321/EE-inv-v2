from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import decode_access_token
from app.models.auth import AuthUser, APIKey
from app.config import settings
from typing import Optional, List
from urllib.parse import quote


security = HTTPBearer(auto_error=False)


def get_auth_token_from_request(request: Request) -> Optional[str]:
    """Get auth token from cookie (Auth Hub) or Authorization header (fallback)"""
    # 1. Check cookie first (Auth Hub)
    token = request.cookies.get("auth_token")
    if token:
        return token
    
    # 2. Check Authorization header (fallback for API calls)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")
    
    return None


def redirect_to_auth_hub(request: Request) -> RedirectResponse:
    """Redirect to Auth Hub with return_to parameter"""
    # Get the full URL including query parameters
    full_url = str(request.url)
    return_to = quote(full_url)
    auth_url = f"{settings.AUTH_HUB_URL}/?return_to={return_to}"
    return RedirectResponse(url=auth_url, status_code=302)


def get_user_id_from_payload(payload: dict) -> Optional[str]:
    """Extract user ID from token payload (supports both Auth Hub and legacy formats)"""
    # Auth Hub uses "userId", legacy uses "sub"
    # CRITICAL: user_id in database is VARCHAR, so convert to string
    user_id = payload.get("userId") or payload.get("sub")
    if user_id is not None:
        # Convert to string - Auth Hub may send integer, but DB expects string
        return str(user_id)
    return None


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> AuthUser:
    """Get current authenticated user from Auth Hub cookie or Authorization header"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Get token from cookie (Auth Hub) or header (fallback)
    token = get_auth_token_from_request(request)
    
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = get_user_id_from_payload(payload)
    if user_id is None:
        raise credentials_exception

    user = db.query(AuthUser).filter(AuthUser.user_id == user_id).first()
    if user is None or not user.active:
        raise credentials_exception

    return user


def get_api_key_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> tuple[AuthUser, APIKey]:
    """
    Get user from API key authentication (for microservices)

    Returns:
        Tuple of (user, api_key)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )

    api_key = credentials.credentials
    if not api_key.startswith("sk_"):
        raise credentials_exception

    # Find API key
    key_record = db.query(APIKey).filter(APIKey.key_id == api_key).first()
    if key_record is None or not key_record.active:
        raise credentials_exception

    # Check expiration
    from datetime import datetime, timezone
    if key_record.expires_at:
        # Handle timezone naive vs aware comparison
        expires_at = key_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key expired",
            )

    # Get user
    user = db.query(AuthUser).filter(AuthUser.user_id == key_record.created_by).first()
    if user is None or not user.active:
        raise credentials_exception

    return user, key_record


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[AuthUser]:
    """Get user if token (cookie or header) or API key is present, otherwise return None"""
    try:
        # Try API Key first (from Authorization header)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer sk_"):
            token = auth_header.replace("Bearer ", "")
            key_record = db.query(APIKey).filter(APIKey.key_id == token).first()
            
            if key_record and key_record.active:
                # Check expiration
                from datetime import datetime, timezone
                expires_at = key_record.expires_at
                if expires_at:
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    if expires_at < datetime.now(timezone.utc):
                        return None
                
                user = db.query(AuthUser).filter(AuthUser.user_id == key_record.created_by).first()
                return user if user and user.active else None
        
        # Try JWT token (from cookie or header)
        token = get_auth_token_from_request(request)
        if token:
            payload = decode_access_token(token)
            if payload:
                user_id = get_user_id_from_payload(payload)
                if user_id:
                    user = db.query(AuthUser).filter(AuthUser.user_id == user_id).first()
                    return user if user and user.active else None
    except Exception:
        pass

    return None


def check_permission(required_permission: str, permissions: List[str]) -> bool:
    """Check if permission is granted"""
    return "all" in permissions or required_permission in permissions


def require_permission(required_permission: str):
    """Dependency to require specific permission"""
    def permission_checker(
        user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
        # Admin has all permissions
        if user.role == "admin":
            return user

        # Check user permissions
        user_permissions = user.app_permissions or []
        if not check_permission(required_permission, user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required",
            )

        return user

    return permission_checker


def get_request_ip(request: Request) -> Optional[str]:
    """Get client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else None

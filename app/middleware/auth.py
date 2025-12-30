from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import decode_access_token
from app.models.auth import AuthUser, APIKey
from typing import Optional, List


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AuthUser:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
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
    """Get user if token or API key is present, otherwise return None"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    try:
        # Try API Key first
        if auth_header.startswith("Bearer sk_"):
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
        
        # Try JWT token
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            payload = decode_access_token(token)
            if payload:
                user_id = payload.get("sub")
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

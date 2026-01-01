import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT access token (Auth Hub compatible)"""
    try:
        # Use JWT_SECRET_KEY (must match Auth Hub's JWT_SECRET)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return "".join([str(secrets.randbelow(10)) for _ in range(settings.OTP_LENGTH)])


def generate_share_token() -> str:
    """Generate a unique share token"""
    return secrets.token_urlsafe(32)


def generate_invoice_number() -> str:
    """Generate a unique invoice number (placeholder - actual implementation will query DB)"""
    # This will be replaced with actual DB logic
    return f"{settings.INVOICE_NUMBER_PREFIX}-{secrets.token_hex(4).upper()}"

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from app.models.auth import AuthUser, APIKey, AuthSession
from app.utils.security import generate_otp, generate_share_token
from app.config import settings
import secrets
import hashlib


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user_by_whatsapp(self, whatsapp: str, name: Optional[str] = None) -> AuthUser:
        """Get or create user by WhatsApp number"""
        user = self.db.query(AuthUser).filter(AuthUser.whatsapp_number == whatsapp).first()
        if user:
            # Update name if provided
            if name and not user.name:
                user.name = name
            self.db.commit()
            self.db.refresh(user)
            return user

        # Create new user
        user_id = f"user_{secrets.token_hex(8)}"
        user = AuthUser(
            user_id=user_id,
            whatsapp_number=whatsapp,
            whatsapp_formatted=whatsapp,
            name=name,
            role="customer",  # Default role
            active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_user_otp(self, user_id: str, otp_code: str) -> None:
        """Set OTP for user"""
        user = self.db.query(AuthUser).filter(AuthUser.user_id == user_id).first()
        if user:
            user.last_otp_code = otp_code
            user.last_otp_at = datetime.utcnow()
            self.db.commit()

    def verify_user_otp(self, whatsapp: str, otp_code: str) -> Optional[AuthUser]:
        """Verify OTP for user"""
        user = self.db.query(AuthUser).filter(AuthUser.whatsapp_number == whatsapp).first()
        if not user:
            return None

        # Check OTP match
        if user.last_otp_code != otp_code:
            return None

        # Check OTP expiration
        if user.last_otp_at:
            expiry_time = user.last_otp_at + timedelta(seconds=settings.OTP_EXPIRE_SECONDS)
            if datetime.utcnow() > expiry_time:
                return None

        # Clear OTP after successful verification
        user.last_otp_code = None
        user.last_login_at = datetime.utcnow()
        self.db.commit()

        return user

    def update_user_role(self, user_id: str, role: str, permissions: Optional[List[str]] = None) -> AuthUser:
        """Update user role and permissions"""
        user = self.db.query(AuthUser).filter(AuthUser.user_id == user_id).first()
        if user:
            user.role = role
            if permissions is not None:
                user.app_permissions = permissions
            self.db.commit()
            self.db.refresh(user)
        return user

    def create_api_key(
        self,
        created_by: str,
        service_name: str,
        app_domain: str,
        permissions: List[str],
        expires_in_days: Optional[int] = None
    ) -> tuple[APIKey, str]:
        """Create a new API key"""
        key_id = f"sk_{secrets.token_urlsafe(32)}"
        key_secret = secrets.token_urlsafe(48)
        key_hash = hashlib.sha256(key_secret.encode()).hexdigest()

        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            service_name=service_name,
            app_domain=app_domain,
            permissions=permissions,
            active=True,
            expires_at=expires_at,
            created_by=created_by,
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)

        return api_key, f"{key_id}.{key_secret}"

    def get_api_keys(self, user_id: str) -> List[APIKey]:
        """Get all API keys for a user"""
        return self.db.query(APIKey).filter(APIKey.created_by == user_id).all()

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        api_key = self.db.query(APIKey).filter(APIKey.key_id == key_id).first()
        if api_key:
            api_key.active = False
            self.db.commit()
            return True
        return False

    def create_session(self, user_id: str, token_hash: str, expires_at: datetime, ip: Optional[str] = None, user_agent: Optional[str] = None) -> AuthSession:
        """Create a new session"""
        session_id = generate_share_token()
        session = AuthSession(
            session_id=session_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip,
            user_agent=user_agent,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        deleted = self.db.query(AuthSession).filter(
            AuthSession.expires_at < datetime.utcnow()
        ).delete()
        self.db.commit()
        return deleted

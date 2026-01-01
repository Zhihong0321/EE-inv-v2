from sqlalchemy.orm import Session
from sqlalchemy import text, cast, String
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from app.models.user import User
from app.models.auth import APIKey, AuthSession
from app.utils.security import generate_otp, generate_share_token
from app.config import settings
import secrets
import hashlib
import json



class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user_by_whatsapp(self, whatsapp: str, name: Optional[str] = None) -> User:
        """
        Get or create user by WhatsApp number
        NOTE: This is legacy method - users should come from Auth Hub/shared DB
        Searches authentication JSON field for WhatsApp number
        """
        # Query user table by searching authentication JSON for WhatsApp number
        # PostgreSQL JSON query: authentication->>'whatsapp' or authentication->>'phone'
        query = text("""
            SELECT id FROM "user" 
            WHERE authentication::text LIKE :whatsapp_pattern
            LIMIT 1
        """)
        result = self.db.execute(query, {"whatsapp_pattern": f"%{whatsapp}%"})
        row = result.fetchone()
        
        if row:
            user = self.db.query(User).filter(User.id == row.id).first()
            # Note: Can't update name/authentication JSON easily - users managed by Auth Hub
            return user

        # Cannot create users - they must exist in shared database
        # This method is deprecated with Auth Hub
        raise ValueError("User not found. Users must be created through Auth Hub/shared database.")

    def set_user_otp(self, user_id: str, otp_code: str) -> None:
        """
        Set OTP for user
        NOTE: User table doesn't have last_otp_code/last_otp_at columns
        OTPs are managed by Auth Hub or otps/auth_hub_otps tables
        This method is deprecated - use Auth Hub OTP system
        """
        # OTPs are now managed by Auth Hub or separate OTP tables
        # User table doesn't store OTP data
        pass

    def verify_user_otp(self, whatsapp: str, otp_code: str) -> Optional[User]:
        """
        Verify OTP for user
        NOTE: User table doesn't store OTP data - check otps or auth_hub_otps tables
        This method is deprecated - use Auth Hub OTP verification
        """
        # Query user by WhatsApp in authentication JSON
        query = text("""
            SELECT id FROM "user" 
            WHERE authentication::text LIKE :whatsapp_pattern
            LIMIT 1
        """)
        result = self.db.execute(query, {"whatsapp_pattern": f"%{whatsapp}%"})
        row = result.fetchone()
        
        if not row:
            return None

        # Check OTP in otps or auth_hub_otps table
        otp_query = text("""
            SELECT expires_at FROM otps 
            WHERE phone_number = :phone AND code = :code
            UNION ALL
            SELECT expires_at FROM auth_hub_otps 
            WHERE phone_number = :phone AND code = :code
            LIMIT 1
        """)
        otp_result = self.db.execute(otp_query, {"phone": whatsapp, "code": otp_code})
        otp_row = otp_result.fetchone()
        
        if not otp_row:
            return None

        # Check expiration
        if otp_row.expires_at:
            expires_at = otp_row.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                return None

        # Get user
        user = self.db.query(User).filter(User.id == row.id).first()
        return user

    def update_user_role(self, user_id: str, role: str, permissions: Optional[List[str]] = None) -> User:
        """
        Update user role and permissions
        NOTE: Role is derived from access_level array, not a direct column
        This method is deprecated - user management handled by Auth Hub
        """
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return None
            
        user = self.db.query(User).filter(User.id == user_id_int).first()
        if user:
            # Update access_level array (role is derived from this)
            # Note: This is a simplified update - full role management should be via Auth Hub
            if permissions is not None:
                user.access_level = permissions
            self.db.commit()
            self.db.refresh(user)
        return user

    def create_api_key(
        self,
        created_by: int,  # Now integer (user.id)
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
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            service_name=service_name,
            app_domain=app_domain,
            permissions=permissions,
            active=True,
            expires_at=expires_at,
            created_by=str(created_by),  # Store as string for compatibility
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)

        return api_key, f"{key_id}.{key_secret}"

    def get_api_keys(self, user_id: str) -> List[APIKey]:
        """Get all API keys for a user"""
        # user_id is string, created_by is stored as string
        return self.db.query(APIKey).filter(APIKey.created_by == user_id).all()

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        api_key = self.db.query(APIKey).filter(APIKey.key_id == key_id).first()
        if api_key:
            api_key.active = False
            self.db.commit()
            return True
        return False

    def create_session(self, user_id: int, token_hash: str, expires_at: datetime, ip: Optional[str] = None, user_agent: Optional[str] = None) -> AuthSession:
        """Create a new session"""
        session_id = generate_share_token()
        session = AuthSession(
            session_id=session_id,
            user_id=user_id,  # Now integer
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
            AuthSession.expires_at < datetime.now(timezone.utc)
        ).delete()
        self.db.commit()
        return deleted

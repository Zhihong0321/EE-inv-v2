"""
User model mapping to production 'user' table
All apps share the same database and use the 'user' table
Auth Hub userId maps to user.id
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ARRAY
from sqlalchemy.sql import func
from app.database import Base
import json
from typing import Optional, List, Dict, Any


class User(Base):
    """
    User model for production 'user' table
    Maps Auth Hub userId to user.id
    """
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)  # Maps to Auth Hub userId
    bubble_id = Column(String, unique=True, nullable=False, index=True)
    last_synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    check_in_report_today = Column(String)
    dealership = Column(String)
    created_date = Column(DateTime(timezone=True))
    linked_agent_profile = Column(String)
    authentication = Column(Text)  # JSON string with email/whatsapp data
    access_level = Column(ARRAY(String))  # Array of permission strings
    user_signed_up = Column(Boolean)
    profile_picture = Column(String)
    modified_date = Column(DateTime(timezone=True))
    agent_code = Column(String)

    # Properties for backward compatibility
    @property
    def user_id(self) -> str:
        """Get user_id as string (for compatibility with existing code)"""
        return str(self.id)

    @property
    def whatsapp_number(self) -> Optional[str]:
        """Extract WhatsApp number from authentication JSON or token payload"""
        if self.authentication:
            try:
                auth_data = json.loads(self.authentication)
                if isinstance(auth_data, dict):
                    if "whatsapp" in auth_data:
                        whatsapp_data = auth_data["whatsapp"]
                        if isinstance(whatsapp_data, dict):
                            return whatsapp_data.get("number") or whatsapp_data.get("phone")
                        return str(whatsapp_data)
                    if "phone" in auth_data:
                        return str(auth_data["phone"])
            except:
                pass
        return None

    @property
    def whatsapp_formatted(self) -> str:
        """Get formatted WhatsApp number"""
        return self.whatsapp_number or ""

    @property
    def name(self) -> Optional[str]:
        """Extract name from authentication JSON or profile"""
        if self.authentication:
            try:
                auth_data = json.loads(self.authentication)
                if isinstance(auth_data, dict):
                    if "name" in auth_data:
                        return auth_data["name"]
                    if "email" in auth_data and isinstance(auth_data["email"], dict):
                        email = auth_data["email"].get("email", "")
                        # Extract name from email if possible
                        if "@" in email:
                            return email.split("@")[0].replace(".", " ").title()
            except:
                pass
        return None

    @property
    def role(self) -> str:
        """Determine role from access_level array"""
        if not self.access_level:
            return "customer"
        
        # Check for admin roles
        admin_roles = ["admin", "superadmin", "ceo"]
        for role in admin_roles:
            if role in self.access_level:
                return "admin"
        
        # Check for agent roles
        agent_roles = ["sales", "agent"]
        for role in agent_roles:
            if role in self.access_level:
                return "agent"
        
        return "customer"

    @property
    def active(self) -> bool:
        """User is active if user_signed_up is True"""
        return self.user_signed_up is True if self.user_signed_up is not None else False

    @property
    def app_permissions(self) -> List[str]:
        """Get app permissions from access_level"""
        return list(self.access_level) if self.access_level else []

    @property
    def last_login_at(self) -> Optional[DateTime]:
        """Not available in user table"""
        return None

    def set_name_from_token(self, name: Optional[str]) -> None:
        """Set name from Auth Hub token if not already set"""
        # Name comes from token payload, not stored in user table
        # This is a no-op for compatibility
        pass

    def set_whatsapp_from_token(self, phone: Optional[str]) -> None:
        """Set WhatsApp from Auth Hub token"""
        # WhatsApp comes from token payload, not stored in user table
        # This is a no-op for compatibility
        pass


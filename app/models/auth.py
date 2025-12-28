from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ARRAY, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class AuthUser(Base):
    __tablename__ = "auth_user"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, nullable=False, index=True)
    whatsapp_number = Column(String, unique=True, nullable=False, index=True)
    whatsapp_formatted = Column(String, nullable=False)
    name = Column(String)
    role = Column(String, nullable=False)  # admin, agent, customer
    active = Column(Boolean, default=True)
    app_permissions = Column(ARRAY(String))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True))
    last_otp_at = Column(DateTime(timezone=True))
    last_otp_code = Column(String)  # For verification (temporary)


class APIKey(Base):
    __tablename__ = "api_key"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String, unique=True, nullable=False, index=True)  # UUID (public)
    key_hash = Column(String, nullable=False)  # Hashed secret
    service_name = Column(String, nullable=False)
    app_domain = Column(String, nullable=False)
    permissions = Column(ARRAY(String))  # ['create_invoice', 'read_invoice', ...]
    active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    created_by = Column(String, ForeignKey("auth_user.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuthSession(Base):
    __tablename__ = "auth_session"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("auth_user.user_id"), index=True)
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

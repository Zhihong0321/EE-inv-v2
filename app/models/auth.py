from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ARRAY, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


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
    created_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuthSession(Base):
    __tablename__ = "auth_session"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

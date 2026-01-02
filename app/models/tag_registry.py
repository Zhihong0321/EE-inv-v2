from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class TagCategory(str, enum.Enum):
    """Tag categories for organizing permissions"""
    APP = "app"  # Application name (e.g., "quote")
    FUNCTION = "function"  # Function name (e.g., "voucher", "package")
    DEPARTMENT = "department"  # Department name (e.g., "sales", "finance")


class TagRegistry(Base):
    """
    Registry of valid tags that can be assigned to users.
    Stores all unique tags with their categories for validation and UI display.
    """
    __tablename__ = "tag_registry"

    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String, unique=True, nullable=False, index=True)  # Unique tag string (e.g., "quote", "voucher")
    category = Column(Enum(TagCategory), nullable=False)  # app, function, or department
    description = Column(String)  # Optional description of what this tag allows
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())




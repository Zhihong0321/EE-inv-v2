from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base

class Package(Base):
    __tablename__ = "package"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=False, index=True)
    
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Numeric(15, 2), nullable=False)
    
    # Storing items as JSON for simplicity in this "Package" definition
    # Structure: [{"description": "Service A", "qty": 1, "unit_price": 100}, ...]
    items = Column(JSON, default=list)

    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ARRAY, JSON
from sqlalchemy.sql import func
from app.database import Base

class Package(Base):
    __tablename__ = "package"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=False, index=True)
    
    # Actual columns from database schema (verified)
    last_synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    linked_package_item = Column(ARRAY(String))  # Array of bubble_ids
    name = Column(String)  # Package name
    created_date = Column(DateTime(timezone=True))
    price = Column(Numeric)
    panel = Column(String)  # Panel rating/reference
    active = Column(Boolean)
    modified_date = Column(DateTime(timezone=True))
    need_approval = Column(Boolean)
    invoice_desc = Column(Text)  # Description for invoice items
    panel_qty = Column(Integer)  # Panel quantity
    created_by = Column(String)
    max_discount = Column(Integer)
    type = Column(String)  # e.g., "Residential"
    special = Column(Boolean)
    password = Column(String)
    description = Column(Text)  # Package description
    items = Column(JSON)  # JSON array (verified as json in DB)

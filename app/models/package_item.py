from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class PackageItem(Base):
    __tablename__ = "package_item"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=False, index=True)
    
    last_synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    total_cost = Column(Integer)
    created_by = Column(String)
    modified_date = Column(DateTime(timezone=True))
    created_date = Column(DateTime(timezone=True))
    product = Column(String)  # References product.bubble_id
    qty = Column(Integer)
    sort = Column(Integer)
    inventory = Column(Boolean)





from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Brand(Base):
    __tablename__ = "brand"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=True, index=True)
    
    name = Column(String)
    created_by = Column(String)
    modified_date = Column(DateTime(timezone=True))
    created_date = Column(DateTime(timezone=True))
    logo = Column(String)
    synced_at = Column(DateTime(timezone=True))



from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text
from sqlalchemy.sql import func
from app.database import Base

class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=False, index=True)
    
    last_synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    linked_brand = Column(String)  # References brand.bubble_id
    inventory = Column(Boolean)
    image = Column(String)
    modified_date = Column(DateTime(timezone=True))
    created_date = Column(DateTime(timezone=True))
    warranty_name = Column(String)
    active = Column(Boolean)
    cost_price = Column(Numeric)
    selling_price = Column(Numeric)
    description = Column(Text)
    linked_category = Column(String)
    name = Column(String)
    warranty_link = Column(String)
    label = Column(String)
    pdf_product = Column(String)
    product_warranty_desc = Column(Text)
    solar_output_rating = Column(Integer)
    created_by = Column(String)
    inverter_rating = Column(Integer)










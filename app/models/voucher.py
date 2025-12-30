from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ARRAY
from sqlalchemy.sql import func
from app.database import Base

class Voucher(Base):
    __tablename__ = "voucher"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=False, index=True)
    voucher_code = Column(String, unique=True, index=True)
    title = Column(String)
    discount_amount = Column(Numeric(15, 2))
    discount_percent = Column(Integer)
    invoice_description = Column(Text)
    active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

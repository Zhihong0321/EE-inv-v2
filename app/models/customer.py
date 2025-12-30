from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Customer(Base):
    __tablename__ = "customer"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, unique=True, nullable=False, index=True)

    # Basic info
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)

    # Address
    address = Column(Text)
    city = Column(String)
    state = Column(String)
    postcode = Column(String)

    # ID verification
    ic_number = Column(String)

    # Reference to old system
    linked_seda_registration = Column(String)
    linked_old_customer = Column(String)

    # Metadata
    notes = Column(Text)
    created_by = Column(String, ForeignKey("auth_user.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

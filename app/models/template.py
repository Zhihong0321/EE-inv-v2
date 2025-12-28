from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class InvoiceTemplate(Base):
    __tablename__ = "invoice_template"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=False, index=True)
    template_name = Column(String, nullable=False)

    # Company info
    company_name = Column(String, nullable=False)
    company_address = Column(Text, nullable=False)
    company_phone = Column(String)
    company_email = Column(String)
    sst_registration_no = Column(String, nullable=False)
    bank_name = Column(String)
    bank_account_no = Column(String)
    bank_account_name = Column(String)

    # Visual
    logo_url = Column(String)

    # Terms
    terms_and_conditions = Column(Text)

    # Metadata
    active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_by = Column(String, ForeignKey("auth_user.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

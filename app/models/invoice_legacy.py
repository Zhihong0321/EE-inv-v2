from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Invoice(Base):
    __tablename__ = "invoice"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=False, index=True)
    
    # Metadata
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_date = Column(DateTime(timezone=True))
    modified_date = Column(DateTime(timezone=True))
    created_by = Column(String)
    
    # Core Invoice Details
    invoice_id = Column(Integer, index=True)  # The human-readable ID
    invoice_date = Column(DateTime(timezone=True))
    type = Column(String)  # BUSINESS, PV CUSTOMER, etc.
    description = Column(Text)
    amount = Column(Numeric(15, 2))
    
    # Financials / Payments
    paid = Column(Boolean, default=False)
    amount_eligible_for_comm = Column(Numeric(15, 2))
    percent_of_total_amount = Column(Numeric(5, 2))
    first_payment = Column("1st_payment", Integer)
    first_payment_date = Column("1st_payment_date", DateTime(timezone=True))
    second_payment = Column("2nd_payment", Integer)
    last_payment_date = Column(DateTime(timezone=True))
    full_payment_date = Column(DateTime(timezone=True))
    commission_paid = Column(Boolean, default=False)
    
    # Statuses
    approval_status = Column(String)
    case_status = Column(String)
    stock_status = Column(String)
    stock_status_inv = Column(String)
    need_approval = Column(Boolean, default=False)
    
    # Relationships (String-based bubble_ids)
    linked_customer = Column(String, index=True)
    linked_agent = Column(String, index=True)
    linked_package = Column(String, index=True)
    linked_seda_registration = Column(String, index=True)
    linked_agreement = Column(String)
    linked_payment = Column(ARRAY(String))
    linked_invoice_item = Column(ARRAY(String))
    linked_voucher = Column(ARRAY(String))
    
    # Solar Specific
    panel_qty = Column(Integer)
    panel_rating = Column(Integer)
    panel_description = Column(Text)  # mapped from eligible_amount_description
    estimated_saving = Column(Numeric(15, 2))
    estimated_new_bill_amount = Column(Numeric(15, 2))
    achieved_monthly_anp = Column(Numeric(15, 2))
    
    # Other
    dealercode = Column(String)
    logs = Column(Text)
    visit = Column(Integer)
    performance_tier_month = Column(Integer)
    performance_tier_year = Column(Integer)
    first_payment_extra = Column("1st_payment__", String)
    second_payment_extra = Column("2nd_payment__", String)
    stock_status_extra = Column("stock_status__", String)
    
    # Items Relationship
    items = relationship("InvoiceItem", primaryjoin="Invoice.bubble_id == foreign(InvoiceItem.linked_invoice)", backref="invoice")

class InvoiceItem(Base):
    __tablename__ = "invoice_item"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=False, index=True)
    
    # Metadata
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_date = Column(DateTime(timezone=True))
    modified_date = Column(DateTime(timezone=True))
    created_by = Column(String)
    
    # Item Details
    description = Column(Text)
    qty = Column(Integer)
    unit_price = Column(Numeric(15, 2))
    amount = Column(Numeric(15, 2))
    sort = Column(Integer)
    
    # Flags / Types
    is_a_package = Column(Boolean, default=False)
    inv_item_type = Column(String)  # Discount, etc.
    
    # Relationships
    linked_invoice = Column(String, index=True)
    linked_package = Column(String)
    linked_voucher = Column(String)
    voucher_remark = Column(Text)
    epp = Column(Integer)


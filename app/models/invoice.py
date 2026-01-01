from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, and_
from app.database import Base


class InvoiceNew(Base):
    __tablename__ = "invoice_new"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=False, index=True)

    # Template
    template_id = Column(String)  # References invoice_template.bubble_id (no FK - new table)

    # Customer
    customer_id = Column(Integer, ForeignKey("customer.id"), index=True)

    # Customer snapshot
    customer_name_snapshot = Column(String, nullable=False)
    customer_address_snapshot = Column(Text)
    customer_phone_snapshot = Column(String)
    customer_email_snapshot = Column(String)

    # Agent
    agent_id = Column(String)  # References agent.bubble_id (old system)
    agent_name_snapshot = Column(String)

    # Package
    package_id = Column(String)  # References package.bubble_id (old system)
    package_name_snapshot = Column(String)

    # Invoice details
    invoice_number = Column(String, unique=True, nullable=False, index=True)
    invoice_date = Column(String, nullable=False)  # Using String for DATE to avoid timezone issues
    due_date = Column(String)

    # Amounts
    subtotal = Column(Numeric(15, 2), nullable=False, default=0)
    agent_markup = Column(Numeric(15, 2), default=0)  # Hidden markup added to subtotal
    sst_rate = Column(Numeric(5, 2), default=8)  # 8% SST by default
    sst_amount = Column(Numeric(15, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(15, 2), nullable=False, default=0)
    discount_fixed = Column(Numeric(15, 2), default=0)  # Fixed amount discount
    discount_percent = Column(Numeric(5, 2))
    voucher_code = Column(String)
    voucher_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)

    # Status
    status = Column(String, default="draft")  # draft, sent, viewed, paid, partial, overdue, cancelled
    paid_amount = Column(Numeric(15, 2), default=0)

    # Notes
    internal_notes = Column(Text)
    customer_notes = Column(Text)

    # Share link
    share_token = Column(String, unique=True, index=True)
    share_enabled = Column(Boolean, default=False)
    share_expires_at = Column(DateTime(timezone=True))
    share_access_count = Column(Integer, default=0)

    # Reference to old invoice
    linked_old_invoice = Column(String)  # Store bubble_id reference to legacy invoice (no FK constraint)

    # Migration status
    migration_status = Column(String, default="new")  # new, migrated, processed

    # Metadata
    created_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    sent_at = Column(DateTime(timezone=True))
    viewed_at = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))

    # Relationships
    items = relationship("InvoiceNewItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("InvoicePaymentNew", back_populates="invoice", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class InvoiceNewItem(Base):
    __tablename__ = "invoice_new_item"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=False, index=True)

    invoice_id = Column(String, ForeignKey("invoice_new.bubble_id", ondelete="CASCADE"), index=True)

    # Product reference (from old system)
    product_id = Column(String)  # References product.bubble_id (READ-ONLY)
    product_name_snapshot = Column(String)

    # Item details
    description = Column(Text, nullable=False)
    qty = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    total_price = Column(Numeric(15, 2), nullable=False)

    # Item type: package, discount, voucher, adjustment, addon
    item_type = Column(String, default="package")  # NEW: Distinguish item types

    # Sort order for display
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    invoice = relationship("InvoiceNew", back_populates="items")


class InvoicePaymentNew(Base):
    __tablename__ = "invoice_payment_new"

    id = Column(Integer, primary_key=True, index=True)
    bubble_id = Column(String, unique=True, nullable=False, index=True)

    invoice_id = Column(String, ForeignKey("invoice_new.bubble_id", ondelete="CASCADE"), index=True)

    # Payment details
    amount = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(String)  # 'bank_transfer', 'cash', 'card', 'epp', 'online', etc.
    payment_date = Column(String, nullable=False)  # Using String for DATE
    reference_no = Column(String)
    bank_name = Column(String)
    notes = Column(Text)

    # Status
    status = Column(String, default="pending")  # pending, verified, rejected
    verified_by = Column(Integer, ForeignKey("user.id"))
    verified_at = Column(DateTime(timezone=True))

    # Attachments
    attachment_urls = Column(ARRAY(String))

    # Metadata
    created_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    invoice = relationship("InvoiceNew", back_populates="payments")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)  # 'invoice', 'customer', 'template', etc.
    entity_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # 'create', 'update', 'delete', 'view', etc.
    user_id = Column(Integer, ForeignKey("user.id"))
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    ip_address = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

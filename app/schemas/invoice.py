from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class InvoiceItemCreate(BaseModel):
    product_id: Optional[str] = None
    product_name_snapshot: Optional[str] = None
    description: str = Field(..., min_length=1)
    qty: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    sort_order: Optional[int] = 0


class InvoiceItemUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=1)
    qty: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    sort_order: Optional[int] = None


class InvoiceItemResponse(BaseModel):
    bubble_id: str
    product_id: Optional[str] = None
    product_name_snapshot: Optional[str] = None
    description: str
    qty: Decimal
    unit_price: Decimal
    discount_percent: Decimal
    total_price: Decimal
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class InvoicePaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., min_length=1)
    payment_date: str
    reference_no: Optional[str] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None
    attachment_urls: Optional[List[str]] = None


class InvoicePaymentUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0)
    payment_method: Optional[str] = Field(None, min_length=1)
    payment_date: Optional[str] = None
    reference_no: Optional[str] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class InvoicePaymentResponse(BaseModel):
    bubble_id: str
    amount: Decimal
    payment_method: str
    payment_date: str
    reference_no: Optional[str] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None
    status: str
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    customer_id: Optional[str] = None
    template_id: Optional[str] = None

    # If customer_id not provided, create new customer
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None

    # Agent and package
    agent_id: Optional[str] = None
    package_id: Optional[str] = None

    # Invoice details
    invoice_number: Optional[str] = None  # Auto-generated if not provided
    invoice_date: Optional[str] = None  # Defaults to today
    due_date: Optional[str] = None

    # Discount and voucher
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    voucher_code: Optional[str] = None
    apply_sst: Optional[bool] = False

    # Items
    items: List[InvoiceItemCreate] = Field(default_factory=list)

    # Notes
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None


class InvoiceUpdate(BaseModel):
    customer_id: Optional[str] = None
    template_id: Optional[str] = None
    agent_id: Optional[str] = None
    package_id: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    voucher_code: Optional[str] = None
    status: Optional[str] = None
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None


class InvoiceOnTheFlyRequest(BaseModel):
    package_id: str
    discount_fixed: Optional[Decimal] = Field(Decimal(0), ge=0)
    discount_percent: Optional[Decimal] = Field(Decimal(0), ge=0, le=100)
    discount_given: Optional[str] = None  # String format: "500 10%" or "500" or "10%"
    apply_sst: bool = False
    template_id: Optional[str] = None
    voucher_code: Optional[str] = None
    agent_markup: Optional[Decimal] = Field(Decimal(0), ge=0)
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    epp_fee_amount: Optional[Decimal] = Field(None, ge=0)  # Total EPP fee amount
    epp_fee_description: Optional[str] = None  # Combined description: "Maybank EPP 60 Months - RM15000, ..."


class InvoiceResponse(BaseModel):
    bubble_id: str
    invoice_number: str
    invoice_date: str
    due_date: Optional[str] = None
    subtotal: Decimal
    agent_markup: Optional[Decimal] = None
    sst_rate: Decimal
    sst_amount: Decimal
    discount_amount: Decimal
    discount_fixed: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    voucher_code: Optional[str] = None
    voucher_amount: Decimal
    total_amount: Decimal
    status: str
    paid_amount: Decimal
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name_snapshot: str
    customer_phone_snapshot: Optional[str] = None
    customer_email_snapshot: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name_snapshot: Optional[str] = None
    package_id: Optional[str] = None
    package_name_snapshot: Optional[str] = None
    share_token: Optional[str] = None
    share_enabled: bool
    linked_old_invoice: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Include items and payments in full response
    items: List[InvoiceItemResponse] = []
    payments: List[InvoicePaymentResponse] = []

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    invoices: List[InvoiceResponse]


class GenerateShareLinkResponse(BaseModel):
    success: bool
    share_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: Optional[str] = None


class InvoiceFromURLRequest(BaseModel):
    """Schema for invoice creation from URL parameters (Solar Business)"""
    # Required Solar Business parameters
    package_id: str
    panel_qty: Optional[int] = None
    panel_rating: Optional[str] = None  # e.g., "450W"
    discount_given: Optional[str] = None  # Discount amount or percent

    # Optional customer info
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None

    # Other options
    template_id: Optional[str] = None
    apply_sst: Optional[bool] = False

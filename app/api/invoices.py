from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.database import get_db
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    InvoiceItemCreate, InvoiceItemUpdate, InvoiceItemResponse,
    InvoicePaymentCreate, InvoicePaymentUpdate, InvoicePaymentResponse,
    InvoiceListResponse, GenerateShareLinkResponse,
    InvoiceOnTheFlyRequest
)
from app.repositories.invoice_repo import InvoiceRepository
from app.repositories.customer_repo import CustomerRepository
from app.middleware.auth import get_current_user, get_api_key_user, get_optional_user, get_request_ip
from app.models.user import User
from app.config import settings
from app.utils.html_generator import generate_invoice_html
from app.utils.pdf_generator import generate_invoice_pdf, sanitize_filename

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_data: InvoiceCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new invoice (auto-create customer if customer_id not provided)"""
    invoice_repo = InvoiceRepository(db)
    customer_repo = CustomerRepository(db)

    # Get or create customer
    customer = None
    if invoice_data.customer_id:
        customer = customer_repo.get_by_id(invoice_data.customer_id)

    # If no customer_id, create new customer
    if not customer:
        customer = customer_repo.create(
            name=invoice_data.customer_name or "Customer",
            phone=invoice_data.customer_phone,
            email=invoice_data.customer_email,
            address=invoice_data.customer_address,
            created_by=current_user.id,
        )

    # Calculate item totals
    items = []
    for item in invoice_data.items:
        qty = Decimal(str(item.qty))
        unit_price = Decimal(str(item.unit_price))
        discount_percent = Decimal(str(item.discount_percent or 0))
        total_price = qty * unit_price * (1 - discount_percent / Decimal(100))

        items.append({
            "product_id": item.product_id,
            "product_name_snapshot": item.product_name_snapshot,
            "description": item.description,
            "qty": item.qty,
            "unit_price": item.unit_price,
            "discount_percent": item.discount_percent,
            "total_price": total_price,
            "sort_order": item.sort_order,
        })

    # Get agent and package names (from old system tables)
    agent_name = None
    package_name = None

    if invoice_data.agent_id:
        # Query agent from old system
        result = db.execute(
            text("SELECT name FROM agent WHERE bubble_id = :agent_id"),
            {"agent_id": invoice_data.agent_id}
        )
        row = result.fetchone()
        if row:
            agent_name = row[0]

    if invoice_data.package_id:
        # Query package from old system
        # Note: package table has 'name' column, not 'package_name'
        result = db.execute(
            text("SELECT name FROM package WHERE bubble_id = :package_id"),
            {"package_id": invoice_data.package_id}
        )
        row = result.fetchone()
        if row:
            package_name = row[0]

    # Create invoice
    invoice = invoice_repo.create(
        customer_id=customer.customer_id,
        template_id=invoice_data.template_id,
        agent_id=invoice_data.agent_id,
        package_id=invoice_data.package_id,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        discount_percent=invoice_data.discount_percent,
        voucher_code=invoice_data.voucher_code,
        items=items,
        internal_notes=invoice_data.internal_notes,
        customer_notes=invoice_data.customer_notes,
        customer_name_snapshot=customer.name,
        customer_address_snapshot=customer.address,
        customer_phone_snapshot=customer.phone,
        customer_email_snapshot=customer.email,
        agent_name_snapshot=agent_name,
        package_name_snapshot=package_name,
        created_by=current_user.id,
        apply_sst=invoice_data.apply_sst,
    )

    return invoice


@router.get("/vouchers/validate/{code}")
def validate_voucher(
    code: str, 
    package_id: str, 
    db: Session = Depends(get_db)
):
    """Validate a voucher code for a specific package"""
    from app.models.voucher import Voucher
    from app.models.package import Package
    
    voucher = db.query(Voucher).filter(Voucher.voucher_code == code, Voucher.active == True).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Invalid or inactive voucher code")
    
    package = db.query(Package).filter(Package.bubble_id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
        
    discount_amount = Decimal(0)
    if voucher.discount_amount:
        discount_amount = voucher.discount_amount
    elif voucher.discount_percent:
        discount_amount = package.price * (Decimal(voucher.discount_percent) / Decimal(100))
        
    return {
        "voucher_code": voucher.voucher_code,
        "discount_amount": float(discount_amount),
        "discount_percent": voucher.discount_percent,
        "title": voucher.title or voucher.voucher_code
    }


@router.post("/on-the-fly", response_model=dict)
async def create_invoice_on_the_fly(
    request_data: InvoiceOnTheFlyRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Create a new invoice on the fly for microservices or quick creation.
    Returns the shareable URL and invoice details.
    """
    invoice_repo = InvoiceRepository(db)
    
    # Parse discount_given string into discount_fixed and discount_percent
    # Input format: "500 10%" or "500" or "10%"
    from decimal import Decimal
    
    discount_fixed = Decimal(0)
    discount_percent = Decimal(0)
    
    if request_data.discount_given:
        discount_str = request_data.discount_given.strip()
        parts = discount_str.replace('+', ' ').split()
        
        for part in parts:
            part = part.strip()
            if '%' in part:
                discount_percent = Decimal(part.replace('%', ''))
            else:
                try:
                    discount_fixed = Decimal(part.replace('RM', '').replace(',', ''))
                except:
                    pass

    try:
        invoice = invoice_repo.create_on_the_fly(
            package_id=request_data.package_id,
            discount_fixed=discount_fixed,
            discount_percent=discount_percent,
            apply_sst=request_data.apply_sst,
            template_id=request_data.template_id,
            voucher_code=request_data.voucher_code,
            agent_markup=request_data.agent_markup,
            customer_name=request_data.customer_name,
            customer_phone=request_data.customer_phone,
            customer_address=request_data.customer_address,
            epp_fee_amount=request_data.epp_fee_amount,
            epp_fee_description=request_data.epp_fee_description,
            created_by=current_user.id if current_user else None
        )
        # Build base URL for share link
        base_url = str(request.base_url).rstrip("/")
        share_url = f"{base_url}/view/{invoice.share_token}"

        response = {
            "success": True,
            "invoice_link": share_url,
            "invoice_number": invoice.invoice_number,
            "bubble_id": invoice.bubble_id,
            "total_amount": float(invoice.total_amount),
        }

        # Show markup info if user is logged in
        if current_user:
            response["agent_markup"] = float(invoice.agent_markup)
            response["subtotal_with_markup"] = float(invoice.subtotal)

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")


@router.get("", response_model=InvoiceListResponse)
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List invoices with filters"""
    invoice_repo = InvoiceRepository(db)
    invoices, total = invoice_repo.get_all(
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
        agent_id=agent_id,
        date_from=date_from,
        date_to=date_to,
    )

    return InvoiceListResponse(
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        invoices=invoices,
    )


@router.get("/{bubble_id}", response_model=InvoiceResponse)
def get_invoice(
    bubble_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get invoice by ID"""
    invoice_repo = InvoiceRepository(db)
    invoice = invoice_repo.get_by_id(bubble_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice


@router.get("/{bubble_id}/pdf")
def download_invoice_pdf(
    bubble_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download invoice as PDF (authenticated endpoint).
    
    Returns PDF file with filename: {company_name}_{invoice_number}.pdf
    """
    invoice_repo = InvoiceRepository(db)
    invoice = invoice_repo.get_by_id(bubble_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Fetch template data
    template_data = {}
    if invoice.template_id:
        template = invoice_repo.get_template(invoice.template_id)
        if template:
            template_data = template
    
    # Fallback to default template if none found
    if not template_data:
        template_data = invoice_repo.get_default_template_data() or {}
    
    # Convert invoice to dict for html_generator
    invoice_dict = invoice.to_dict()
    # Add items to invoice_dict
    invoice_dict["items"] = [
        {
            "description": item.description,
            "qty": float(item.qty),
            "unit_price": float(item.unit_price),
            "total_price": float(item.total_price)
        } for item in invoice.items
    ]
    
    # Generate HTML (without PDF download button for cleaner PDF)
    html_content = generate_invoice_html(invoice_dict, template_data, share_token=None, invoice_id=None)
    
    # Generate PDF
    try:
        # Get base URL for resolving relative URLs (fonts, images)
        base_url = str(request.base_url).rstrip("/")
        pdf_bytes = generate_invoice_pdf(html_content, page_size='A4', base_url=base_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )
    
    # Generate filename
    company_name = template_data.get('company_name', 'Invoice')
    invoice_number = invoice.invoice_number
    filename = sanitize_filename(company_name, invoice_number)
    
    # Return PDF as response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@router.get("/number/{invoice_number}", response_model=InvoiceResponse)
def get_invoice_by_number(
    invoice_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get invoice by invoice number"""
    invoice_repo = InvoiceRepository(db)
    invoice = invoice_repo.get_by_number(invoice_number)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice


@router.put("/{bubble_id}", response_model=InvoiceResponse)
def update_invoice(
    bubble_id: str,
    invoice_data: InvoiceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update invoice"""
    invoice_repo = InvoiceRepository(db)

    # Build update dict from non-None values
    update_data = {k: v for k, v in invoice_data.model_dump(exclude_none=True).items() if v is not None}

    invoice = invoice_repo.update(bubble_id, **update_data)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice


@router.delete("/{bubble_id}")
def delete_invoice(
    bubble_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete invoice"""
    invoice_repo = InvoiceRepository(db)
    success = invoice_repo.delete(bubble_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return {"message": "Invoice deleted successfully"}


# Invoice Items
@router.post("/{bubble_id}/items", response_model=InvoiceItemResponse, status_code=status.HTTP_201_CREATED)
def add_invoice_item(
    bubble_id: str,
    item_data: InvoiceItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add item to invoice"""
    invoice_repo = InvoiceRepository(db)

    # Verify invoice exists
    invoice = invoice_repo.get_by_id(bubble_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    item = invoice_repo.add_item(
        invoice_id=bubble_id,
        product_id=item_data.product_id,
        product_name_snapshot=item_data.product_name_snapshot,
        description=item_data.description,
        qty=Decimal(str(item_data.qty)),
        unit_price=Decimal(str(item_data.unit_price)),
        discount_percent=Decimal(str(item_data.discount_percent or 0)),
        sort_order=item_data.sort_order,
    )

    return item


@router.put("/{bubble_id}/items/{item_id}", response_model=InvoiceItemResponse)
def update_invoice_item(
    bubble_id: str,
    item_id: str,
    item_data: InvoiceItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update invoice item"""
    invoice_repo = InvoiceRepository(db)

    update_data = {k: v for k, v in item_data.model_dump(exclude_none=True).items() if v is not None}
    if "qty" in update_data:
        update_data["qty"] = Decimal(str(update_data["qty"]))
    if "unit_price" in update_data:
        update_data["unit_price"] = Decimal(str(update_data["unit_price"]))
    if "discount_percent" in update_data:
        update_data["discount_percent"] = Decimal(str(update_data["discount_percent"]))

    item = invoice_repo.update_item(item_id, **update_data)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return item


@router.delete("/{bubble_id}/items/{item_id}")
def delete_invoice_item(
    bubble_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete invoice item"""
    invoice_repo = InvoiceRepository(db)
    success = invoice_repo.delete_item(item_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return {"message": "Item deleted successfully"}


# Invoice Payments
@router.post("/{bubble_id}/payments", response_model=InvoicePaymentResponse, status_code=status.HTTP_201_CREATED)
def add_payment(
    bubble_id: str,
    payment_data: InvoicePaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add payment to invoice"""
    invoice_repo = InvoiceRepository(db)

    # Verify invoice exists
    invoice = invoice_repo.get_by_id(bubble_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    payment = invoice_repo.add_payment(
        invoice_id=bubble_id,
        amount=Decimal(str(payment_data.amount)),
        payment_method=payment_data.payment_method,
        payment_date=payment_data.payment_date,
        reference_no=payment_data.reference_no,
        bank_name=payment_data.bank_name,
        notes=payment_data.notes,
        attachment_urls=payment_data.attachment_urls,
        created_by=current_user.id,
    )

    return payment


@router.post("/{bubble_id}/share", response_model=GenerateShareLinkResponse)
def generate_share_link(
    bubble_id: str,
    expires_in_days: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a shareable link for the invoice"""
    invoice_repo = InvoiceRepository(db)

    invoice = invoice_repo.generate_share_link(bubble_id, expires_in_days)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Build share URL using request base URL
    base_url = str(request.base_url).rstrip("/")
    share_url = f"{base_url}/view/{invoice.share_token}"

    return GenerateShareLinkResponse(
        success=True,
        share_url=share_url,
        expires_at=invoice.share_expires_at,
        message="Share link generated successfully"
    )


@router.post("/{bubble_id}/mark-sent", response_model=InvoiceResponse)
def mark_invoice_sent(
    bubble_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark invoice as sent"""
    invoice_repo = InvoiceRepository(db)

    invoice = invoice_repo.update(bubble_id, status="sent", sent_at=datetime.now(timezone.utc))

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice


@router.post("/{bubble_id}/mark-paid", response_model=InvoiceResponse)
def mark_invoice_paid(
    bubble_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark invoice as fully paid"""
    invoice_repo = InvoiceRepository(db)

    invoice = invoice_repo.update(bubble_id, status="paid", paid_at=datetime.now(timezone.utc))

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice

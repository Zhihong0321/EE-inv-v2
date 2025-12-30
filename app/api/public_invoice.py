from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, Union
from app.database import get_db
from app.schemas.invoice import InvoiceResponse
from app.repositories.invoice_repo import InvoiceRepository
from app.utils.html_generator import generate_invoice_html
from app.services.whatsapp_service import whatsapp_service
from app.config import settings

router = APIRouter(tags=["Public Invoice Share"])


@router.get("/view/{share_token}", response_class=Union[HTMLResponse, InvoiceResponse])
def view_shared_invoice(
    share_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Public view of invoice via share link (returns HTML for browsers, JSON for others)"""
    invoice_repo = InvoiceRepository(db)
    invoice = invoice_repo.get_by_share_token(share_token)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or link expired"
        )

    # Record view
    invoice_repo.record_view(invoice.bubble_id)

    # Check accept header for HTML
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        # Fetch template data
        template_data = {}
        if invoice.template_id:
            template = invoice_repo.get_template(invoice.template_id)
            if template:
                template_data = template
        
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
        
        html_content = generate_invoice_html(invoice_dict, template_data)
        return HTMLResponse(
            content=html_content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    return invoice


@router.post("/edit/{share_token}", response_model=dict)
async def request_edit_access(
    share_token: str,
    phone: str,
    db: Session = Depends(get_db)
):
    """
    Request OTP to edit shared invoice via WhatsApp
    
    Phone number must match customer's phone number
    """
    invoice_repo = InvoiceRepository(db)

    invoice = invoice_repo.get_by_share_token(share_token)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or link expired"
        )

    # Check if phone matches customer's phone (if available)
    if invoice.customer_phone_snapshot:
        # Simple check - phone number (digits only)
        from app.utils.helpers import format_phone_number
        formatted_phone = format_phone_number(phone)
        formatted_customer_phone = format_phone_number(invoice.customer_phone_snapshot)

        if formatted_phone != formatted_customer_phone:
            # For security, don't reveal the actual phone number
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Phone number does not match customer's phone number"
            )

    # Generate OTP and send via WhatsApp
    from app.utils.security import generate_otp
    from app.repositories.auth_repo import AuthRepository

    auth_repo = AuthRepository(db)
    otp_code = generate_otp()

    # Store OTP temporarily (use customer name for reference)
    # Create temporary user for OTP verification
    user = auth_repo.get_or_create_user_by_whatsapp(phone, invoice.customer_name_snapshot)
    auth_repo.set_user_otp(user.user_id, otp_code)

    # Send OTP
    sent = await whatsapp_service.send_otp(
        phone=phone,
        otp_code=otp_code,
        name=invoice.customer_name_snapshot
    )

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )

    return {
        "success": True,
        "message": "OTP sent to your WhatsApp",
        "expires_in": settings.OTP_EXPIRE_SECONDS
    }


@router.post("/edit/{share_token}/verify", response_model=dict)
def verify_edit_access(
    share_token: str,
    phone: str,
    otp_code: str,
    db: Session = Depends(get_db)
):
    """
    Verify OTP and get edit token for shared invoice
    """
    invoice_repo = InvoiceRepository(db)
    auth_repo = AuthRepository(db)

    # Verify OTP
    user = auth_repo.verify_user_otp(phone, otp_code)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP"
        )

    # Get invoice
    invoice = invoice_repo.get_by_share_token(share_token)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or link expired"
        )

    # Create temporary JWT token for editing
    from app.utils.security import create_access_token
    from datetime import timedelta
    edit_token = create_access_token(
        data={
            "sub": user.user_id,
            "edit_invoice": invoice.bubble_id,
            "scope": "invoice_edit"
        },
        expires_delta=timedelta(hours=1)
    )

    return {
        "success": True,
        "edit_token": edit_token,
        "message": "Edit access granted. Valid for 1 hour."
    }

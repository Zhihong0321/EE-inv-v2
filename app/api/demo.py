from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import random
from datetime import date, timedelta
from app.database import get_db
from app.models.customer import Customer
from app.models.package import Package
from app.models.template import InvoiceTemplate
from app.utils.html_generator import generate_invoice_html

router = APIRouter(prefix="/demo", tags=["Demo"])

@router.get("/generate-invoice", response_class=HTMLResponse)
def generate_random_invoice_view(db: Session = Depends(get_db)):
    """
    Generates a demo invoice view by randomly selecting a Customer and a Package.
    Also loads the default template (or first available).
    """
    
    # 1. Get Random Customer
    customer_count = db.query(Customer).count()
    if customer_count > 0:
        random_offset = random.randint(0, customer_count - 1)
        customer = db.query(Customer).offset(random_offset).first()
    else:
        # Dummy customer if none exists
        customer = type('obj', (object,), {
            "name": "Demo Customer (No DB Data)",
            "address": "123 Demo Street, Tech City",
            "phone": "+60123456789",
            "email": "demo@example.com"
        })

    # 2. Get Random Package
    package_count = db.query(Package).count()
    if package_count > 0:
        random_offset = random.randint(0, package_count - 1)
        package = db.query(Package).offset(random_offset).first()
        
        # Parse items if they are JSON
        items = package.items if package.items else []
        # If items is empty list but package has price, create a default item
        if not items and package.price:
            items = [{
                "description": package.name,
                "qty": 1,
                "unit_price": float(package.price),
                "total_price": float(package.price)
            }]
    else:
        # Dummy package if none exists
        package = type('obj', (object,), {
            "name": "Standard Service Package",
            "price": 150.00,
            "items": [
                {"description": "Consultation Fee", "qty": 1, "unit_price": 50.00, "total_price": 50.00},
                {"description": "Service Implementation", "qty": 2, "unit_price": 50.00, "total_price": 100.00}
            ]
        })
        items = package.items

    # 3. Get Template (Default or First)
    template_model = db.query(InvoiceTemplate).filter(InvoiceTemplate.is_default == True).first()
    if not template_model:
        template_model = db.query(InvoiceTemplate).first()
    
    if template_model:
        template_data = {
            "company_name": template_model.company_name,
            "company_address": template_model.company_address,
            "company_phone": template_model.company_phone,
            "company_email": template_model.company_email,
            "sst_registration_no": template_model.sst_registration_no,
            "bank_name": template_model.bank_name,
            "bank_account_no": template_model.bank_account_no,
            "bank_account_name": template_model.bank_account_name,
            "logo_url": template_model.logo_url,
            "terms_and_conditions": template_model.terms_and_conditions,
            "disclaimer": template_model.disclaimer
        }
    else:
        # Fallback template
        template_data = {
            "company_name": "My Demo Company",
            "company_address": "Suite 101, Business Park",
            "company_phone": "+603-1234 5678",
            "sst_registration_no": "ST1234567890",
            "bank_name": "Maybank",
            "bank_account_no": "512345678901",
            "bank_account_name": "My Demo Company Sdn Bhd",
            "terms_and_conditions": "Payment due within 14 days.\nGoods sold are not returnable.",
            "disclaimer": "This is a computer generated invoice."
        }

    # 4. Construct Invoice Data
    # Calculate totals
    subtotal = sum(item['total_price'] for item in items)
    sst_rate = 8.0
    sst_amount = subtotal * (sst_rate / 100)
    total_amount = subtotal + sst_amount

    invoice_data = {
        "invoice_number": f"INV-{random.randint(10000, 99999)}",
        "invoice_date": date.today().strftime("%Y-%m-%d"),
        "due_date": (date.today() + timedelta(days=14)).strftime("%Y-%m-%d"),
        "customer_name_snapshot": customer.name,
        "customer_address_snapshot": customer.address,
        "items": items,
        "subtotal": subtotal,
        "sst_rate": sst_rate,
        "sst_amount": sst_amount,
        "total_amount": total_amount
    }

    # 5. Generate HTML
    return generate_invoice_html(invoice_data, template_data)

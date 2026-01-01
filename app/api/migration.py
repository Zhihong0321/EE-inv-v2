from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
from app.database import get_db
from app.repositories.invoice_repo import InvoiceRepository
from app.repositories.customer_repo import CustomerRepository
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/migration", tags=["Data Migration"])


@router.post("/migrate-old-invoices", response_model=dict)
def migrate_old_invoices(
    limit: int = 10,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manual migration service to process old invoices into new system
    
    This will migrate up to `limit` unmigrated old invoices
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform migration"
        )

    invoice_repo = InvoiceRepository(db)
    customer_repo = CustomerRepository(db)

    # Get unmigrated old invoices
    query = text("""
        SELECT i.*, 
               json_agg(json_build_object(
                   'bubble_id', ii.bubble_id,
                   'description', ii.description,
                   'qty', ii.qty,
                   'unit_price', ii.unit_price,
                   'amount', ii.amount
               )) as items
        FROM invoice i
        LEFT JOIN invoice_item ii ON i.bubble_id = ii.linked_invoice
        WHERE NOT EXISTS (
            SELECT 1 FROM invoice_new inv
            WHERE inv.linked_old_invoice = i.bubble_id
        )
        GROUP BY i.bubble_id
        LIMIT :limit
    """)
    
    result = db.execute(query, {"limit": limit})
    old_invoices = [dict(row) for row in result]

    if not old_invoices:
        return {
            "success": True,
            "migrated": 0,
            "message": "No more unmigrated invoices found"
        }

    migrated_count = 0
    failed_count = 0
    errors = []

    for old_invoice in old_invoices:
        try:
            # Get customer info from seda_registration
            customer = None
            if old_invoice.get("linked_seda_registration"):
                seda_query = text("""
                    SELECT * FROM seda_registration 
                    WHERE bubble_id = :seda_id
                """)
                seda_result = db.execute(seda_query, {"seda_id": old_invoice["linked_seda_registration"]}).fetchone()
                if seda_result:
                    seda_data = dict(seda_result)

                    # Create or get customer
                    existing_customer = customer_repo.get_by_id(old_invoice["linked_seda_registration"])
                    if not existing_customer:
                        customer = customer_repo.create(
                            customer_id=old_invoice["linked_seda_registration"],
                            name=seda_data.get("e_contact_name", "Customer"),
                            phone=seda_data.get("e_contact_no"),
                            email=seda_data.get("email") or seda_data.get("e_email"),
                            address=seda_data.get("installation_address"),
                            city=seda_data.get("city"),
                            state=seda_data.get("state"),
                            ic_number=seda_data.get("ic_no"),
                            linked_seda_registration=old_invoice["linked_seda_registration"],
                            created_by=current_user.id,
                        )
                    else:
                        customer = existing_customer

            # If no customer from seda_registration, create a placeholder
            if not customer:
                customer = customer_repo.create(
                    name=f"Customer {old_invoice['invoice_id']}",
                    created_by=current_user.id,
                )

            # Get agent info
            agent_name = None
            if old_invoice.get("linked_agent"):
                agent_query = text("SELECT name FROM agent WHERE bubble_id = :agent_id")
                agent_result = db.execute(agent_query, {"agent_id": old_invoice["linked_agent"]}).fetchone()
                if agent_result:
                    agent_name = agent_result[0]

            # Get package info
            package_name = None
            if old_invoice.get("linked_package"):
                # Note: package table has 'name' column, not 'package_name'
                package_query = text("SELECT name FROM package WHERE bubble_id = :package_id")
                package_result = db.execute(package_query, {"package_id": old_invoice["linked_package"]}).fetchone()
                if package_result:
                    package_name = package_result[0]

            # Get items
            items = []
            if old_invoice.get("items"):
                for item in old_invoice["items"]:
                    if item:  # item might be None
                        items.append({
                            "product_id": None,
                            "product_name_snapshot": None,
                            "description": item.get("description", ""),
                            "qty": item.get("qty", 1),
                            "unit_price": item.get("unit_price", 0),
                            "discount_percent": 0,
                            "total_price": item.get("amount", 0),
                            "sort_order": 0,
                        })

            # Map status from old to new system
            old_status = old_invoice.get("approval_status", "draft")
            if old_status in ["No Approval Needed", "Approved"]:
                new_status = "sent"
            elif old_status == "draft":
                new_status = "draft"
            else:
                new_status = "draft"

            # Create new invoice
            invoice = invoice_repo.create(
                customer_id=customer.customer_id,
                template_id=None,  # Use default template
                agent_id=old_invoice.get("linked_agent"),
                package_id=old_invoice.get("linked_package"),
                invoice_number=old_invoice.get("invoice_id", f"INV-{old_invoice['id']}"),
                invoice_date=str(old_invoice.get("invoice_date", ""))[:10] if old_invoice.get("invoice_date") else None,
                due_date=str(old_invoice.get("last_payment_date", ""))[:10] if old_invoice.get("last_payment_date") else None,
                discount_percent=None,
                voucher_code=None,
                items=items,
                internal_notes=f"Migrated from old invoice {old_invoice['bubble_id']}",
                customer_notes=old_invoice.get("description", ""),
                customer_name_snapshot=customer.name,
                customer_address_snapshot=customer.address,
                customer_phone_snapshot=customer.phone,
                customer_email_snapshot=customer.email,
                agent_name_snapshot=agent_name,
                package_name_snapshot=package_name,
                created_by=current_user.user_id,
                linked_old_invoice=old_invoice["bubble_id"],
            )

            # Update status and migration flag
            invoice_repo.update(
                invoice.bubble_id,
                status=new_status,
                migration_status="processed"
            )

            migrated_count += 1

        except Exception as e:
            failed_count += 1
            errors.append({
                "invoice_id": old_invoice.get("bubble_id"),
                "error": str(e)
            })
            db.rollback()
            continue

    return {
        "success": True,
        "migrated": migrated_count,
        "failed": failed_count,
        "errors": errors,
        "message": f"Migrated {migrated_count} invoices successfully"
    }


@router.get("/status", response_model=dict)
def get_migration_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get migration status"""
    # Count old invoices
    old_count_query = text("SELECT COUNT(*) FROM invoice")
    old_count = db.execute(old_count_query).scalar()

    # Count new invoices
    new_count_query = text("SELECT COUNT(*) FROM invoice_new")
    new_count = db.execute(new_count_query).scalar()

    # Count migrated invoices
    migrated_query = text("SELECT COUNT(*) FROM invoice_new WHERE linked_old_invoice IS NOT NULL")
    migrated_count = db.execute(migrated_query).scalar()

    # Count unmigrated invoices
    unmigrated_query = text("""
        SELECT COUNT(*) 
        FROM invoice i
        WHERE NOT EXISTS (
            SELECT 1 FROM invoice_new inv
            WHERE inv.linked_old_invoice = i.bubble_id
        )
    """)
    unmigrated_count = db.execute(unmigrated_query).scalar()

    return {
        "old_invoice_count": old_count,
        "new_invoice_count": new_count,
        "migrated_count": migrated_count,
        "unmigrated_count": unmigrated_count,
        "migration_percentage": round((migrated_count / old_count * 100), 2) if old_count > 0 else 0,
    }

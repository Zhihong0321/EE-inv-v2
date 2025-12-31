from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.models.invoice import InvoiceNew, InvoiceNewItem, InvoicePaymentNew, AuditLog
from app.models.package import Package
from app.models.voucher import Voucher
from app.models.customer import Customer
from app.models.template import InvoiceTemplate
from app.utils.security import generate_share_token
from app.config import settings
import secrets
import json


class InvoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def _generate_invoice_number(self) -> str:
        """Generate next invoice number"""
        # Find the highest invoice number
        last_invoice = self.db.query(InvoiceNew).order_by(
            InvoiceNew.invoice_number.desc()
        ).first()

        if last_invoice:
            # Extract number part (after INV-)
            try:
                last_num = int(last_invoice.invoice_number.replace(settings.INVOICE_NUMBER_PREFIX + "-", ""))
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1

        # Format with leading zeros
        num_str = str(next_num).zfill(settings.INVOICE_NUMBER_LENGTH)
        return f"{settings.INVOICE_NUMBER_PREFIX}-{num_str}"

    def create(
        self,
        customer_id: Optional[str] = None,
        template_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        package_id: Optional[str] = None,
        invoice_number: Optional[str] = None,
        invoice_date: Optional[str] = None,
        due_date: Optional[str] = None,
        discount_percent: Optional[Decimal] = None,
        voucher_code: Optional[str] = None,
        items: Optional[List[dict]] = None,
        internal_notes: Optional[str] = None,
        customer_notes: Optional[str] = None,
        customer_name_snapshot: str = "",
        customer_address_snapshot: Optional[str] = None,
        customer_phone_snapshot: Optional[str] = None,
        customer_email_snapshot: Optional[str] = None,
        agent_name_snapshot: Optional[str] = None,
        package_name_snapshot: Optional[str] = None,
        created_by: Optional[str] = None,
        linked_old_invoice: Optional[str] = None,
    ) -> InvoiceNew:
        """Create a new invoice"""
        bubble_id = f"inv_{secrets.token_hex(8)}"

        if not invoice_number:
            invoice_number = self._generate_invoice_number()

        if not invoice_date:
            invoice_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Create invoice
        invoice = InvoiceNew(
            bubble_id=bubble_id,
            template_id=template_id,
            customer_id=customer_id,
            customer_name_snapshot=customer_name_snapshot,
            customer_address_snapshot=customer_address_snapshot,
            customer_phone_snapshot=customer_phone_snapshot,
            customer_email_snapshot=customer_email_snapshot,
            agent_id=agent_id,
            agent_name_snapshot=agent_name_snapshot,
            package_id=package_id,
            package_name_snapshot=package_name_snapshot,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            discount_percent=discount_percent,
            voucher_code=voucher_code,
            internal_notes=internal_notes,
            customer_notes=customer_notes,
            sst_rate=settings.DEFAULT_SST_RATE,
            created_by=created_by,
            linked_old_invoice=linked_old_invoice,
        )

        # SST override logic
        if template_id:
            from app.models.template import InvoiceTemplate
            template = self.db.query(InvoiceTemplate).filter(InvoiceTemplate.bubble_id == template_id).first()
            if template and not template.apply_sst:
                invoice.sst_rate = Decimal(0)
        else:
            from app.models.template import InvoiceTemplate
            default_template = self.db.query(InvoiceTemplate).filter(InvoiceTemplate.is_default == True).first()
            if default_template and not default_template.apply_sst:
                invoice.sst_rate = Decimal(0)
            elif not default_template:
                invoice.sst_rate = Decimal(0)

        self.db.add(invoice)
        self.db.flush()  # Get the invoice ID

        # Add items
        if items:
            for item_data in items:
                item = InvoiceNewItem(
                    bubble_id=f"item_{secrets.token_hex(8)}",
                    invoice_id=bubble_id,
                    product_id=item_data.get("product_id"),
                    product_name_snapshot=item_data.get("product_name_snapshot"),
                    description=item_data["description"],
                    qty=Decimal(str(item_data["qty"])),
                    unit_price=Decimal(str(item_data["unit_price"])),
                    discount_percent=Decimal(str(item_data.get("discount_percent", 0))),
                    total_price=Decimal(str(item_data["total_price"])),
                    sort_order=item_data.get("sort_order", 0),
                )
                self.db.add(item)

        # Calculate totals
        self._calculate_invoice_totals(invoice)
        self.db.commit()
        self.db.refresh(invoice)

        # Audit log
        self._create_audit_log("invoice_new", bubble_id, "create", created_by, None, invoice.to_dict())

        return invoice

    def _calculate_invoice_totals(self, invoice: InvoiceNew) -> None:
        """Calculate invoice totals"""
        # Get all items from session/relationship to ensure we see unflushed items
        items = invoice.items

        # If items list is empty, try querying as fallback
        if not items:
            items = self.db.query(InvoiceNewItem).filter(
                InvoiceNewItem.invoice_id == invoice.bubble_id
            ).all()

        # Calculate base subtotal from items (including negative prices from discount/voucher items)
        subtotal = sum(item.total_price for item in items) if items else Decimal(0)
        invoice.subtotal = subtotal

        # Calculate discount amount from discount items (negative prices already in subtotal)
        discount_items = [item for item in items if hasattr(item, 'item_type') and item.item_type == 'discount']
        discount_from_items = sum(abs(item.total_price) for item in discount_items)

        # Calculate voucher amount from voucher items (negative prices already in subtotal)
        voucher_items = [item for item in items if hasattr(item, 'item_type') and item.item_type == 'voucher']
        voucher_from_items = sum(abs(item.total_price) for item in voucher_items)

        # Update invoice fields to match item amounts (for reference)
        invoice.discount_amount = discount_from_items
        invoice.voucher_amount = voucher_from_items

        # Calculate SST (on subtotal, which already includes negative prices)
        # Note: If there are discount/voucher items, they're already negative in subtotal
        taxable_amount = subtotal
        invoice.sst_amount = taxable_amount * (invoice.sst_rate / Decimal(100)) if taxable_amount > 0 else Decimal(0)

        # Calculate total
        invoice.total_amount = taxable_amount + invoice.sst_amount

    def create_on_the_fly(
        self,
        package_id: str,
        discount_fixed: Decimal = Decimal(0),
        discount_percent: Decimal = Decimal(0),
        apply_sst: bool = True,
        template_id: Optional[str] = None,
        voucher_code: Optional[str] = None,
        agent_markup: Decimal = Decimal(0),
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_address: Optional[str] = None,
        epp_fee_amount: Optional[Decimal] = None,
        epp_fee_description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> InvoiceNew:
        """Create an invoice on the fly based on a package and other parameters"""
        
        # 1. Fetch Package
        package = self.db.query(Package).filter(Package.bubble_id == package_id).first()
        if not package:
            raise ValueError(f"Package not found: {package_id}")

        # 2. Handle Customer
        customer_id = None
        if customer_name:
            # Try to find existing customer by name and phone
            customer = self.db.query(Customer).filter(Customer.name == customer_name).first()
            if not customer:
                customer_id_str = f"cust_{secrets.token_hex(4)}"
                customer = Customer(
                    customer_id=customer_id_str,
                    name=customer_name,
                    phone=customer_phone,
                    address=customer_address,
                    created_by=created_by
                )
                self.db.add(customer)
                self.db.flush()
            customer_id = customer.id
            cust_name_snapshot = customer.name
            cust_phone_snapshot = customer.phone
            cust_address_snapshot = customer.address
            cust_email_snapshot = customer.email
        else:
            cust_name_snapshot = "Sample Quotation"
            cust_phone_snapshot = customer_phone
            cust_address_snapshot = customer_address
            cust_email_snapshot = None

        # 3. Handle Voucher
        voucher_amount = Decimal(0)
        if voucher_code:
            voucher = self.db.query(Voucher).filter(Voucher.voucher_code == voucher_code, Voucher.active == True).first()
            if voucher:
                if voucher.discount_amount:
                    voucher_amount = voucher.discount_amount
                elif voucher.discount_percent:
                    # Will be calculated based on package price later if needed, 
                    # but usually it's a fixed amount or applied to total.
                    # For now, let's assume it's applied to the package price.
                    voucher_amount = package.price * (Decimal(voucher.discount_percent) / Decimal(100))

        # 4. Handle Template and SST
        sst_rate = Decimal(0)
        if apply_sst:
            sst_rate = Decimal(str(settings.DEFAULT_SST_RATE))
            # Optional: if template has a specific rate, use it? 
            # For now, just use default 8% if apply_sst is True.

        # 5. Create Invoice
        bubble_id = f"inv_{secrets.token_hex(8)}"
        invoice_number = self._generate_invoice_number()
        
        invoice = InvoiceNew(
            bubble_id=bubble_id,
            invoice_number=invoice_number,
            invoice_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            customer_id=customer_id,
            customer_name_snapshot=cust_name_snapshot,
            customer_phone_snapshot=cust_phone_snapshot,
            customer_address_snapshot=cust_address_snapshot,
            customer_email_snapshot=cust_email_snapshot,
            package_id=package_id,
            package_name_snapshot=package.name if hasattr(package, 'name') else (package.invoice_desc or f"Package {package.bubble_id}"),
            template_id=template_id,
            discount_fixed=discount_fixed,
            discount_percent=discount_percent,
            agent_markup=agent_markup,
            voucher_code=voucher_code,
            voucher_amount=voucher_amount,
            sst_rate=sst_rate,
            status="draft",
            created_by=created_by,
            share_token=secrets.token_urlsafe(16),
            share_enabled=True,
            share_expires_at=datetime.now(timezone.utc) + timedelta(days=settings.SHARE_LINK_EXPIRY_DAYS)
        )

        # Ensure template_id is set
        invoice.template_id = template_id
        
        self.db.add(invoice)
        self.db.flush()

        # 6. Add Items from Package
        # Package table does NOT have an items column - always create single item from invoice_desc and price
        # Add markup to the item
        unit_price = (package.price or Decimal(0)) + agent_markup
        item = InvoiceNewItem(
            bubble_id=f"item_{secrets.token_hex(8)}",
            invoice=invoice,  # Use relationship for immediate update
            description=package.invoice_desc or (package.name if hasattr(package, 'name') else f"Package {package.bubble_id}") or "Package Item",
            qty=Decimal(1),
            unit_price=unit_price,
            total_price=unit_price,
            item_type="package",  # Mark as package item
            sort_order=0
        )
        self.db.add(item)

        # 6b. Create Discount Items (if discount exists)
        # Create TWO separate discount items: one for fixed, one for percentage
        # Discount should be visible as invoice item with negative price
        discount_sort_order = 100  # Start discount items at sort_order 100

        # Create FIXED discount item separately
        if discount_fixed and discount_fixed > 0:
            fixed_discount_item = InvoiceNewItem(
                bubble_id=f"item_{secrets.token_hex(8)}",
                invoice=invoice,  # Use relationship for immediate update
                description=f"Discount (RM {discount_fixed})",
                qty=Decimal(1),
                unit_price=-discount_fixed,  # Negative price for discount
                total_price=-discount_fixed,
                item_type="discount",
                sort_order=discount_sort_order
            )
            self.db.add(fixed_discount_item)
            discount_sort_order += 1

        # Create PERCENT discount item separately
        if discount_percent and discount_percent > 0:
            percent_amount = package.price * (discount_percent / Decimal(100))
            percent_discount_item = InvoiceNewItem(
                bubble_id=f"item_{secrets.token_hex(8)}",
                invoice=invoice,  # Use relationship for immediate update
                description=f"Discount ({discount_percent}%)",
                qty=Decimal(1),
                unit_price=-percent_amount,  # Negative price for discount
                total_price=-percent_amount,
                item_type="discount",
                sort_order=discount_sort_order
            )
            self.db.add(percent_discount_item)
            discount_sort_order += 1

        # 6c. Create Voucher Item (if voucher exists)
        # Voucher should be visible as invoice item with negative price
        if voucher_code and voucher_amount > 0:
            voucher_item = InvoiceNewItem(
                bubble_id=f"item_{secrets.token_hex(8)}",
                invoice=invoice,  # Use relationship for immediate update
                description=f"Voucher ({voucher_code})",
                qty=Decimal(1),
                unit_price=-voucher_amount,  # Negative price for voucher
                total_price=-voucher_amount,
                item_type="voucher",
                sort_order=101  # Show after discount
            )
            self.db.add(voucher_item)

        # 6d. Create EPP Fee Item (if EPP fees exist)
        # EPP fee should be visible as invoice item with positive price
        if epp_fee_amount and epp_fee_amount > 0 and epp_fee_description:
            # Ensure epp_fee_amount is Decimal
            epp_fee_decimal = Decimal(str(epp_fee_amount)) if not isinstance(epp_fee_amount, Decimal) else epp_fee_amount
            epp_fee_item = InvoiceNewItem(
                bubble_id=f"item_{secrets.token_hex(8)}",
                invoice=invoice,  # Use relationship for immediate update
                description=f"Bank Processing Fee ({epp_fee_description})",
                qty=Decimal(1),
                unit_price=epp_fee_decimal,
                total_price=epp_fee_decimal,
                item_type="epp_fee",  # Mark as EPP fee item
                sort_order=200  # Show after voucher
            )
            self.db.add(epp_fee_item)

        # Note: Markup is NOT visible as item (user requirement: "invisible to client")
        # Markup is already added to package price above

        # 7. Finalize
        self._calculate_invoice_totals(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        
        # Audit log
        new_values = {c.name: getattr(invoice, c.name) for c in invoice.__table__.columns}
        # Convert Decimals to float for JSON serialization in audit log
        for k, v in new_values.items():
            if isinstance(v, Decimal):
                new_values[k] = float(v)
            elif isinstance(v, datetime):
                new_values[k] = v.isoformat()
        
        import json
        self._create_audit_log("invoice_new", bubble_id, "create_on_the_fly", created_by, None, json.dumps(new_values))

        return invoice

    def get_by_id(self, bubble_id: str) -> Optional[InvoiceNew]:
        """Get invoice by ID"""
        return self.db.query(InvoiceNew).filter(InvoiceNew.bubble_id == bubble_id).first()

    def get_by_number(self, invoice_number: str) -> Optional[InvoiceNew]:
        """Get invoice by invoice number"""
        return self.db.query(InvoiceNew).filter(InvoiceNew.invoice_number == invoice_number).first()

    def get_template(self, template_id: str) -> Optional[dict]:
        """Get template data by ID"""
        from sqlalchemy import text
        result = self.db.execute(
            text("SELECT * FROM invoice_template WHERE bubble_id = :id"),
            {"id": template_id}
        ).first()
        return result._asdict() if result else None

    def get_by_share_token(self, share_token: str) -> Optional[InvoiceNew]:
        """Get invoice by share token"""
        invoice = self.db.query(InvoiceNew).filter(
            InvoiceNew.share_token == share_token
        ).first()

        # Check if share is valid
        if invoice and invoice.share_enabled:
            if invoice.share_expires_at and invoice.share_expires_at < datetime.now(timezone.utc):
                return None
            return invoice

        return None

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> tuple[List[InvoiceNew], int]:
        """Get all invoices with filters"""
        query = self.db.query(InvoiceNew)

        if status:
            query = query.filter(InvoiceNew.status == status)
        if customer_id:
            query = query.filter(InvoiceNew.customer_id == customer_id)
        if agent_id:
            query = query.filter(InvoiceNew.agent_id == agent_id)
        if date_from:
            query = query.filter(InvoiceNew.invoice_date >= date_from)
        if date_to:
            query = query.filter(InvoiceNew.invoice_date <= date_to)

        query = query.order_by(InvoiceNew.invoice_date.desc(), InvoiceNew.created_at.desc())

        total = query.count()
        invoices = query.offset(skip).limit(limit).all()
        return invoices, total

    def update(
        self,
        bubble_id: str,
        **kwargs
    ) -> Optional[InvoiceNew]:
        """Update invoice"""
        invoice = self.get_by_id(bubble_id)
        if not invoice:
            return None

        old_data = invoice.to_dict()

        for key, value in kwargs.items():
            if hasattr(invoice, key) and value is not None:
                setattr(invoice, key, value)

        invoice.updated_at = datetime.now(timezone.utc)

        # Recalculate totals
        self._calculate_invoice_totals(invoice)

        self.db.commit()
        self.db.refresh(invoice)

        # Audit log
        self._create_audit_log("invoice_new", bubble_id, "update", invoice.created_by, old_data, invoice.to_dict())

        return invoice

    def delete(self, bubble_id: str) -> bool:
        """Delete invoice"""
        invoice = self.get_by_id(bubble_id)
        if not invoice:
            return False

        old_data = invoice.to_dict()

        # Delete related items and payments (cascade)
        self.db.query(InvoiceNewItem).filter(InvoiceNewItem.invoice_id == bubble_id).delete()
        self.db.query(InvoicePaymentNew).filter(InvoicePaymentNew.invoice_id == bubble_id).delete()

        self.db.delete(invoice)
        self.db.commit()

        # Audit log
        self._create_audit_log("invoice_new", bubble_id, "delete", invoice.created_by, old_data, None)

        return True

    def add_item(
        self,
        invoice_id: str,
        product_id: Optional[str],
        product_name_snapshot: Optional[str],
        description: str,
        qty: Decimal,
        unit_price: Decimal,
        discount_percent: Decimal = Decimal(0),
        sort_order: int = 0,
    ) -> InvoiceNewItem:
        """Add item to invoice"""
        item = InvoiceNewItem(
            bubble_id=f"item_{secrets.token_hex(8)}",
            invoice_id=invoice_id,
            product_id=product_id,
            product_name_snapshot=product_name_snapshot,
            description=description,
            qty=qty,
            unit_price=unit_price,
            discount_percent=discount_percent,
            total_price=qty * unit_price * (1 - discount_percent / Decimal(100)),
            sort_order=sort_order,
        )
        self.db.add(item)

        # Recalculate invoice totals
        invoice = self.get_by_id(invoice_id)
        if invoice:
            self._calculate_invoice_totals(invoice)

        self.db.commit()
        self.db.refresh(item)
        return item

    def update_item(
        self,
        item_id: str,
        **kwargs
    ) -> Optional[InvoiceNewItem]:
        """Update invoice item"""
        item = self.db.query(InvoiceNewItem).filter(
            InvoiceNewItem.bubble_id == item_id
        ).first()

        if not item:
            return None

        for key, value in kwargs.items():
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)

        # Recalculate total price
        item.total_price = item.qty * item.unit_price * (1 - item.discount_percent / Decimal(100))

        # Recalculate invoice totals
        invoice = self.get_by_id(item.invoice_id)
        if invoice:
            self._calculate_invoice_totals(invoice)

        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_item(self, item_id: str) -> bool:
        """Delete invoice item"""
        item = self.db.query(InvoiceNewItem).filter(
            InvoiceNewItem.bubble_id == item_id
        ).first()

        if not item:
            return False

        invoice_id = item.invoice_id
        self.db.delete(item)

        # Recalculate invoice totals
        invoice = self.get_by_id(invoice_id)
        if invoice:
            self._calculate_invoice_totals(invoice)

        self.db.commit()
        return True

    def add_payment(
        self,
        invoice_id: str,
        amount: Decimal,
        payment_method: str,
        payment_date: str,
        reference_no: Optional[str] = None,
        bank_name: Optional[str] = None,
        notes: Optional[str] = None,
        attachment_urls: Optional[List[str]] = None,
        created_by: Optional[str] = None,
    ) -> InvoicePaymentNew:
        """Add payment to invoice"""
        payment = InvoicePaymentNew(
            bubble_id=f"pay_{secrets.token_hex(8)}",
            invoice_id=invoice_id,
            amount=amount,
            payment_method=payment_method,
            payment_date=payment_date,
            reference_no=reference_no,
            bank_name=bank_name,
            notes=notes,
            attachment_urls=attachment_urls,
            created_by=created_by,
        )
        self.db.add(payment)

        # Update invoice paid amount
        invoice = self.get_by_id(invoice_id)
        if invoice:
            invoice.paid_amount += amount

            # Update status
            if invoice.paid_amount >= invoice.total_amount:
                invoice.status = "paid"
                invoice.paid_at = datetime.now(timezone.utc)
            elif invoice.paid_amount > 0:
                invoice.status = "partial"

        self.db.commit()
        self.db.refresh(payment)
        return payment

    def generate_share_link(
        self,
        bubble_id: str,
        expires_in_days: Optional[int] = None
    ) -> Optional[InvoiceNew]:
        """Generate a shareable link for invoice"""
        invoice = self.get_by_id(bubble_id)
        if not invoice:
            return None

        # Generate share token
        share_token = generate_share_token()
        invoice.share_token = share_token
        invoice.share_enabled = True

        # Set expiry
        if expires_in_days:
            invoice.share_expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        else:
            invoice.share_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.SHARE_LINK_EXPIRY_DAYS)

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def record_view(self, bubble_id: str) -> None:
        """Record that invoice was viewed via share link"""
        invoice = self.get_by_id(bubble_id)
        if invoice:
            invoice.viewed_at = datetime.now(timezone.utc)
            invoice.share_access_count += 1
            self.db.commit()

    def get_unmigrated_old_invoices(self, limit: int = 100) -> List[dict]:
        """Get old invoices that haven't been migrated yet"""
        # Query from the old invoice table using raw SQL
        query = """
            SELECT i.*, array_agg(jsonb_build_object(
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
        """
        result = self.db.execute(query, {"limit": limit})
        return [dict(row) for row in result]

    def _create_audit_log(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        user_id: Optional[str],
        old_values: Optional[dict],
        new_values: Optional[dict],
        ip_address: Optional[str] = None,
    ) -> None:
        """Create an audit log entry"""
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=ip_address,
        )
        self.db.add(log)
        self.db.commit()


# Monkey patch to_dict method for SQLAlchemy models
def to_dict(model):
    return {c.name: getattr(model, c.name) for c in model.__table__.columns}

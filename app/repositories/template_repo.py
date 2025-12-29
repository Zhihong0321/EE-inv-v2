from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.template import InvoiceTemplate
import secrets


class TemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        template_name: str,
        company_name: str,
        company_address: str,
        company_phone: Optional[str] = None,
        company_email: Optional[str] = None,
        sst_registration_no: str = None,
        bank_name: Optional[str] = None,
        bank_account_no: Optional[str] = None,
        bank_account_name: Optional[str] = None,
        logo_url: Optional[str] = None,
        terms_and_conditions: Optional[str] = None,
        disclaimer: Optional[str] = None,
        apply_sst: bool = False,
        is_default: bool = False,
        created_by: Optional[str] = None,
    ) -> InvoiceTemplate:
        """Create a new invoice template"""
        bubble_id = f"tmpl_{secrets.token_hex(8)}"

        # If setting as default, remove default from others
        if is_default:
            self.db.query(InvoiceTemplate).filter(
                InvoiceTemplate.is_default == True
            ).update({"is_default": False})

        template = InvoiceTemplate(
            bubble_id=bubble_id,
            template_name=template_name,
            company_name=company_name,
            company_address=company_address,
            company_phone=company_phone,
            company_email=company_email,
            sst_registration_no=sst_registration_no,
            bank_name=bank_name,
            bank_account_no=bank_account_no,
            bank_account_name=bank_account_name,
            logo_url=logo_url,
            terms_and_conditions=terms_and_conditions,
            disclaimer=disclaimer,
            apply_sst=apply_sst,
            is_default=is_default,
            created_by=created_by,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_by_id(self, bubble_id: str) -> Optional[InvoiceTemplate]:
        """Get template by ID"""
        return self.db.query(InvoiceTemplate).filter(InvoiceTemplate.bubble_id == bubble_id).first()

    def get_default(self) -> Optional[InvoiceTemplate]:
        """Get the default template"""
        return self.db.query(InvoiceTemplate).filter(
            InvoiceTemplate.is_default == True,
            InvoiceTemplate.active == True
        ).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> tuple[List[InvoiceTemplate], int]:
        """Get all templates"""
        query = self.db.query(InvoiceTemplate)

        if active_only:
            query = query.filter(InvoiceTemplate.active == True)

        query = query.order_by(InvoiceTemplate.is_default.desc(), InvoiceTemplate.created_at.desc())

        total = query.count()
        templates = query.offset(skip).limit(limit).all()
        return templates, total

    def update(
        self,
        bubble_id: str,
        **kwargs
    ) -> Optional[InvoiceTemplate]:
        """Update template"""
        template = self.get_by_id(bubble_id)
        if not template:
            return None

        # Handle setting as default
        if kwargs.get("is_default"):
            self.db.query(InvoiceTemplate).filter(
                InvoiceTemplate.is_default == True,
                InvoiceTemplate.bubble_id != bubble_id
            ).update({"is_default": False})

        for key, value in kwargs.items():
            if hasattr(template, key) and value is not None:
                setattr(template, key, value)

        self.db.commit()
        self.db.refresh(template)
        return template

    def delete(self, bubble_id: str) -> bool:
        """Delete template (soft delete - set active=False)"""
        template = self.get_by_id(bubble_id)
        if not template:
            return False

        template.active = False
        template.is_default = False
        self.db.commit()
        return True

    def set_default(self, bubble_id: str) -> Optional[InvoiceTemplate]:
        """Set template as default"""
        # Remove default from all others
        self.db.query(InvoiceTemplate).filter(
            InvoiceTemplate.is_default == True
        ).update({"is_default": False})

        # Set this as default
        template = self.get_by_id(bubble_id)
        if template:
            template.is_default = True
            self.db.commit()
            self.db.refresh(template)

        return template

from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.models.customer import Customer
import secrets


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postcode: Optional[str] = None,
        ic_number: Optional[str] = None,
        linked_seda_registration: Optional[str] = None,
        linked_old_customer: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Customer:
        """Create a new customer"""
        customer_id = f"cust_{secrets.token_hex(8)}"
        customer = Customer(
            customer_id=customer_id,
            name=name,
            phone=phone,
            email=email,
            address=address,
            city=city,
            state=state,
            postcode=postcode,
            ic_number=ic_number,
            linked_seda_registration=linked_seda_registration,
            linked_old_customer=linked_old_customer,
            notes=notes,
            created_by=created_by,
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        return self.db.query(Customer).filter(Customer.customer_id == customer_id).first()

    def get_by_phone(self, phone: str) -> Optional[Customer]:
        """Get customer by phone number"""
        return self.db.query(Customer).filter(Customer.phone == phone).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> tuple[List[Customer], int]:
        """Get all customers with optional search"""
        query = self.db.query(Customer)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Customer.name.ilike(search_term) |
                Customer.phone.ilike(search_term) |
                Customer.email.ilike(search_term)
            )

        total = query.count()
        customers = query.offset(skip).limit(limit).all()
        return customers, total

    def update(
        self,
        customer_id: str,
        **kwargs
    ) -> Optional[Customer]:
        """Update customer"""
        customer = self.get_by_id(customer_id)
        if not customer:
            return None

        for key, value in kwargs.items():
            if hasattr(customer, key) and value is not None:
                setattr(customer, key, value)

        customer.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def delete(self, customer_id: str) -> bool:
        """Delete customer"""
        customer = self.get_by_id(customer_id)
        if not customer:
            return False

        self.db.delete(customer)
        self.db.commit()
        return True

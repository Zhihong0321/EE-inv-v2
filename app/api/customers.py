from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.repositories.customer_repo import CustomerRepository
from app.middleware.auth import get_current_user
from app.models.auth import AuthUser

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_data: CustomerCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new customer"""
    customer_repo = CustomerRepository(db)
    customer = customer_repo.create(
        name=customer_data.name,
        phone=customer_data.phone,
        email=customer_data.email,
        address=customer_data.address,
        city=customer_data.city,
        state=customer_data.state,
        postcode=customer_data.postcode,
        ic_number=customer_data.ic_number,
        linked_seda_registration=customer_data.linked_seda_registration,
        linked_old_customer=customer_data.linked_old_customer,
        notes=customer_data.notes,
        created_by=current_user.user_id,
    )
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer by ID"""
    customer_repo = CustomerRepository(db)
    customer = customer_repo.get_by_id(customer_id)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return customer


@router.get("/phone/{phone}", response_model=CustomerResponse)
def get_customer_by_phone(
    phone: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer by phone number"""
    customer_repo = CustomerRepository(db)
    customer = customer_repo.get_by_phone(phone)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return customer


@router.get("", response_model=dict)
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all customers with optional search"""
    customer_repo = CustomerRepository(db)
    customers, total = customer_repo.get_all(skip=skip, limit=limit, search=search)

    return {
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
        "customers": customers,
    }


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: str,
    customer_data: CustomerUpdate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update customer"""
    customer_repo = CustomerRepository(db)

    # Build update dict from non-None values
    update_data = {k: v for k, v in customer_data.model_dump().items() if v is not None}

    customer = customer_repo.update(customer_id, **update_data)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return customer


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete customer"""
    customer_repo = CustomerRepository(db)
    success = customer_repo.delete(customer_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return {"message": "Customer deleted successfully"}

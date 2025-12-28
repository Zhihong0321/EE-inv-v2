from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, text
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.auth import AuthUser

router = APIRouter(prefix="/api/v1/legacy", tags=["Legacy Data (Read-Only)"])


@router.get("/invoices", response_model=dict)
def list_old_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List old invoices (read-only)"""
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
        GROUP BY i.bubble_id
        ORDER BY i.created_date DESC
        LIMIT :limit OFFSET :skip
    """)
    
    result = db.execute(query, {"limit": limit, "skip": skip})
    invoices = [dict(row) for row in result]
    
    # Get total count
    count_query = text("SELECT COUNT(*) FROM invoice")
    total = db.execute(count_query).scalar()
    
    return {
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
        "invoices": invoices,
    }


@router.get("/invoices/{bubble_id}", response_model=dict)
def get_old_invoice(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get old invoice by ID (read-only)"""
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
        WHERE i.bubble_id = :bubble_id
        GROUP BY i.bubble_id
    """)
    
    result = db.execute(query, {"bubble_id": bubble_id})
    invoice = result.fetchone()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return dict(invoice)


@router.get("/agents", response_model=dict)
def list_old_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List old agents (read-only)"""
    query = text("""
        SELECT * FROM agent
        ORDER BY created_date DESC
        LIMIT :limit OFFSET :skip
    """)
    
    result = db.execute(query, {"limit": limit, "skip": skip})
    agents = [dict(row) for row in result]
    
    # Get total count
    count_query = text("SELECT COUNT(*) FROM agent")
    total = db.execute(count_query).scalar()
    
    return {
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
        "agents": agents,
    }


@router.get("/agents/{bubble_id}", response_model=dict)
def get_old_agent(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get old agent by ID (read-only)"""
    query = text("SELECT * FROM agent WHERE bubble_id = :bubble_id")
    result = db.execute(query, {"bubble_id": bubble_id})
    agent = result.fetchone()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return dict(agent)


@router.get("/packages", response_model=dict)
def list_old_packages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List old packages (read-only)"""
    query = text("""
        SELECT p.*, 
               json_agg(json_build_object(
                   'bubble_id', pi.bubble_id,
                   'product', pi.product,
                   'qty', pi.qty,
                   'total_cost', pi.total_cost
               )) as items
        FROM package p
        LEFT JOIN package_item pi ON p.bubble_id = ANY(pi.linked_package_item)
        GROUP BY p.bubble_id
        ORDER BY p.created_date DESC
        LIMIT :limit OFFSET :skip
    """)
    
    result = db.execute(query, {"limit": limit, "skip": skip})
    packages = [dict(row) for row in result]
    
    # Get total count
    count_query = text("SELECT COUNT(*) FROM package")
    total = db.execute(count_query).scalar()
    
    return {
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
        "packages": packages,
    }


@router.get("/packages/{bubble_id}", response_model=dict)
def get_old_package(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get old package by ID (read-only)"""
    query = text("""
        SELECT p.*, 
               json_agg(json_build_object(
                   'bubble_id', pi.bubble_id,
                   'product', pi.product,
                   'qty', pi.qty,
                   'total_cost', pi.total_cost
               )) as items
        FROM package p
        LEFT JOIN package_item pi ON p.bubble_id = ANY(pi.linked_package_item)
        WHERE p.bubble_id = :bubble_id
        GROUP BY p.bubble_id
    """)
    
    result = db.execute(query, {"bubble_id": bubble_id})
    package = result.fetchone()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    return dict(package)


@router.get("/products", response_model=dict)
def list_old_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List old products (read-only)"""
    query = text("""
        SELECT * FROM product
        WHERE active = true
        ORDER BY created_date DESC
        LIMIT :limit OFFSET :skip
    """)
    
    result = db.execute(query, {"limit": limit, "skip": skip})
    products = [dict(row) for row in result]
    
    # Get total count
    count_query = text("SELECT COUNT(*) FROM product WHERE active = true")
    total = db.execute(count_query).scalar()
    
    return {
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
        "products": products,
    }


@router.get("/products/{bubble_id}", response_model=dict)
def get_old_product(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get old product by ID (read-only)"""
    query = text("SELECT * FROM product WHERE bubble_id = :bubble_id AND active = true")
    result = db.execute(query, {"bubble_id": bubble_id})
    product = result.fetchone()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return dict(product)


@router.get("/seda-registrations", response_model=dict)
def list_old_seda_registrations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List old SEDA registrations (read-only)"""
    query = text("""
        SELECT sr.*,
               json_agg(json_build_object(
                   'bubble_id', inv.bubble_id,
                   'invoice_id', inv.invoice_id,
                   'amount', inv.amount,
                   'invoice_date', inv.invoice_date
               )) as invoices
        FROM seda_registration sr
        LEFT JOIN invoice inv ON sr.bubble_id = inv.linked_seda_registration
        GROUP BY sr.bubble_id
        ORDER BY sr.created_date DESC
        LIMIT :limit OFFSET :skip
    """)
    
    result = db.execute(query, {"limit": limit, "skip": skip})
    registrations = [dict(row) for row in result]
    
    # Get total count
    count_query = text("SELECT COUNT(*) FROM seda_registration")
    total = db.execute(count_query).scalar()
    
    return {
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
        "seda_registrations": registrations,
    }


@router.get("/seda-registrations/{bubble_id}", response_model=dict)
def get_old_seda_registration(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get old SEDA registration by ID (read-only)"""
    query = text("""
        SELECT sr.*,
               json_agg(json_build_object(
                   'bubble_id', inv.bubble_id,
                   'invoice_id', inv.invoice_id,
                   'amount', inv.amount,
                   'invoice_date', inv.invoice_date
               )) as invoices
        FROM seda_registration sr
        LEFT JOIN invoice inv ON sr.bubble_id = inv.linked_seda_registration
        WHERE sr.bubble_id = :bubble_id
        GROUP BY sr.bubble_id
    """)
    
    result = db.execute(query, {"bubble_id": bubble_id})
    registration = result.fetchone()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SEDA registration not found"
        )
    
    return dict(registration)

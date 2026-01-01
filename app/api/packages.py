from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.auth import AuthUser
from app.repositories.package_repo import PackageRepository
from app.schemas.package import (
    PackageCreate,
    PackageUpdate,
    PackageResponse,
    PackageListResponse,
    PackageItemResponse,
    PackageItemCreate,
    PackageItemUpdate,
    ProductResponse,
    ProductListResponse,
    BrandResponse,
    BrandListResponse
)
from decimal import Decimal

router = APIRouter(prefix="/api/v1/packages", tags=["Package Management"])


@router.get("", response_model=PackageListResponse)
def list_packages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: Optional[bool] = Query(None, description="Filter by active status"),
    type: Optional[str] = Query(None, description="Filter by package type"),
    search: Optional[str] = Query(None, description="Search in name, description"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all packages"""
    repo = PackageRepository(db)
    packages, total = repo.list_packages(
        skip=skip,
        limit=limit,
        active_only=active_only,
        package_type=type,
        search=search
    )
    
    # Enrich packages with items
    enriched_packages = []
    for package in packages:
        package_data = PackageResponse.model_validate(package)
        package_dict = package_data.model_dump()
        
        # Get items
        if package.linked_package_item:
            items_query = """
                SELECT 
                    pi.bubble_id,
                    pi.product as product_id,
                    pi.qty,
                    pi.total_cost,
                    pi.sort,
                    pi.inventory,
                    p.name as product_name,
                    b.name as brand_name
                FROM package_item pi
                LEFT JOIN product p ON p.bubble_id = pi.product
                LEFT JOIN brand b ON b.bubble_id = p.linked_brand
                WHERE pi.bubble_id = ANY(:item_ids)
                ORDER BY pi.sort NULLS LAST, pi.created_date
            """
            from sqlalchemy import text
            items = db.execute(text(items_query), {"item_ids": package.linked_package_item}).fetchall()
            package_dict["items"] = [
                {
                    "bubble_id": item.bubble_id,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "brand_name": item.brand_name,
                    "qty": item.qty,
                    "total_cost": item.total_cost,
                    "sort": item.sort,
                    "inventory": item.inventory
                }
                for item in items
            ]
        else:
            package_dict["items"] = []
        
        enriched_packages.append(PackageResponse(**package_dict))
    
    return PackageListResponse(
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        packages=enriched_packages
    )


@router.get("/{bubble_id}", response_model=PackageResponse)
def get_package(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get package by bubble_id"""
    repo = PackageRepository(db)
    package_data = repo.get_package_with_items(bubble_id)
    
    if not package_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    package = package_data["package"]
    package_response = PackageResponse.model_validate(package)
    package_dict = package_response.model_dump()
    
    # Add items
    items = []
    for item in package_data["items"]:
        items.append(PackageItemResponse(
            bubble_id=item["bubble_id"],
            product_id=item.get("product"),
            product_name=item.get("product_name"),
            brand_name=item.get("brand_name"),
            qty=item.get("qty"),
            total_cost=item.get("total_cost"),
            sort=item.get("sort"),
            inventory=item.get("inventory")
        ))
    
    package_dict["items"] = items
    return PackageResponse(**package_dict)


@router.post("", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
def create_package(
    package_data: PackageCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new package"""
    repo = PackageRepository(db)
    
    package = repo.create_package(
        name=package_data.name,
        price=package_data.price,
        panel=package_data.panel,
        panel_qty=package_data.panel_qty,
        package_type=package_data.type,
        active=package_data.active,
        invoice_desc=package_data.invoice_desc,
        description=package_data.description,
        max_discount=package_data.max_discount,
        special=package_data.special,
        need_approval=package_data.need_approval,
        password=package_data.password,
        linked_package_items=package_data.linked_package_items,
        created_by=current_user.user_id
    )
    
    return PackageResponse.model_validate(package)


@router.put("/{bubble_id}", response_model=PackageResponse)
def update_package(
    bubble_id: str,
    package_data: PackageUpdate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update package"""
    repo = PackageRepository(db)
    
    package = repo.update_package(
        bubble_id=bubble_id,
        name=package_data.name,
        price=package_data.price,
        panel=package_data.panel,
        panel_qty=package_data.panel_qty,
        package_type=package_data.type,
        active=package_data.active,
        invoice_desc=package_data.invoice_desc,
        description=package_data.description,
        max_discount=package_data.max_discount,
        special=package_data.special,
        need_approval=package_data.need_approval,
        password=package_data.password,
        linked_package_items=package_data.linked_package_items
    )
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    return PackageResponse.model_validate(package)


@router.delete("/{bubble_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete package"""
    repo = PackageRepository(db)
    
    if not repo.delete_package(bubble_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )


# Package Item endpoints
@router.post("/items", response_model=PackageItemResponse, status_code=status.HTTP_201_CREATED)
def create_package_item(
    item_data: PackageItemCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new package item"""
    repo = PackageRepository(db)
    
    # Verify product exists
    product = repo.get_product(item_data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    item = repo.create_package_item(
        product_id=item_data.product_id,
        qty=item_data.qty,
        total_cost=item_data.total_cost,
        sort=item_data.sort,
        created_by=current_user.user_id
    )
    
    # Get product and brand info
    product = repo.get_product(item.product)
    brand = None
    if product and product.linked_brand:
        brand = repo.get_brand(product.linked_brand)
    
    return PackageItemResponse(
        bubble_id=item.bubble_id,
        product_id=item.product,
        product_name=product.name if product else None,
        brand_name=brand.name if brand else None,
        qty=item.qty,
        total_cost=item.total_cost,
        sort=item.sort,
        inventory=item.inventory
    )


@router.put("/items/{bubble_id}", response_model=PackageItemResponse)
def update_package_item(
    bubble_id: str,
    item_data: PackageItemUpdate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update package item"""
    repo = PackageRepository(db)
    
    if item_data.product_id:
        product = repo.get_product(item_data.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
    
    item = repo.update_package_item(
        bubble_id=bubble_id,
        product_id=item_data.product_id,
        qty=item_data.qty,
        total_cost=item_data.total_cost,
        sort=item_data.sort
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package item not found"
        )
    
    # Get product and brand info
    product = repo.get_product(item.product) if item.product else None
    brand = None
    if product and product.linked_brand:
        brand = repo.get_brand(product.linked_brand)
    
    return PackageItemResponse(
        bubble_id=item.bubble_id,
        product_id=item.product,
        product_name=product.name if product else None,
        brand_name=brand.name if brand else None,
        qty=item.qty,
        total_cost=item.total_cost,
        sort=item.sort,
        inventory=item.inventory
    )


@router.delete("/items/{bubble_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package_item(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete package item"""
    repo = PackageRepository(db)
    
    if not repo.delete_package_item(bubble_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package item not found"
        )


# Product endpoints
@router.get("/products", response_model=ProductListResponse)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True, description="Show only active products"),
    search: Optional[str] = Query(None, description="Search products"),
    brand_id: Optional[str] = Query(None, description="Filter by brand"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all products"""
    repo = PackageRepository(db)
    products, total = repo.list_products(
        skip=skip,
        limit=limit,
        active_only=active_only,
        search=search,
        brand_id=brand_id
    )
    
    # Enrich with brand names
    enriched_products = []
    for product in products:
        product_dict = ProductResponse.model_validate(product).model_dump()
        if product.linked_brand:
            brand = repo.get_brand(product.linked_brand)
            if brand:
                product_dict["brand_name"] = brand.name
        enriched_products.append(ProductResponse(**product_dict))
    
    return ProductListResponse(
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        products=enriched_products
    )


@router.get("/products/{bubble_id}", response_model=ProductResponse)
def get_product(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get product by bubble_id"""
    repo = PackageRepository(db)
    product = repo.get_product(bubble_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product_dict = ProductResponse.model_validate(product).model_dump()
    if product.linked_brand:
        brand = repo.get_brand(product.linked_brand)
        if brand:
            product_dict["brand_name"] = brand.name
    
    return ProductResponse(**product_dict)


# Brand endpoints
@router.get("/brands", response_model=BrandListResponse)
def list_brands(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search brands"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all brands"""
    repo = PackageRepository(db)
    brands, total = repo.list_brands(skip=skip, limit=limit, search=search)
    
    return BrandListResponse(
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        brands=[BrandResponse.model_validate(brand) for brand in brands]
    )


@router.get("/brands/{bubble_id}", response_model=BrandResponse)
def get_brand(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get brand by bubble_id"""
    repo = PackageRepository(db)
    brand = repo.get_brand(bubble_id)
    
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    return BrandResponse.model_validate(brand)



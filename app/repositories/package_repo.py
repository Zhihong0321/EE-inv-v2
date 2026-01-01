from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
import time
import random
from app.models.package import Package
from app.models.package_item import PackageItem
from app.models.product import Product
from app.models.brand import Brand


class PackageRepository:
    def __init__(self, db: Session):
        self.db = db

    def _generate_bubble_id(self) -> str:
        """Generate bubble_id in format: timestampxrandom"""
        timestamp = int(time.time() * 1000)
        random_part = random.randint(100000000000000000, 999999999999999999)
        return f"{timestamp}x{random_part}"

    def list_packages(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: Optional[bool] = None,
        package_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Package], int]:
        """List packages with filters"""
        query = self.db.query(Package)
        
        if active_only is not None:
            query = query.filter(Package.active == active_only)
        
        if package_type:
            query = query.filter(Package.type == package_type)
        
        if search:
            search_filter = or_(
                Package.name.ilike(f"%{search}%"),
                Package.invoice_desc.ilike(f"%{search}%"),
                Package.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        total = query.count()
        packages = query.order_by(Package.created_date.desc().nullslast(), Package.id.desc()).offset(skip).limit(limit).all()
        
        return packages, total

    def get_package(self, bubble_id: str) -> Optional[Package]:
        """Get package by bubble_id"""
        return self.db.query(Package).filter(Package.bubble_id == bubble_id).first()

    def get_package_with_items(self, bubble_id: str) -> Optional[dict]:
        """Get package with related items"""
        package = self.get_package(bubble_id)
        if not package:
            return None
        
        result = {
            "package": package,
            "items": []
        }
        
        # Get package items
        if package.linked_package_item:
            items_query = text("""
                SELECT 
                    pi.*,
                    p.name as product_name,
                    p.linked_brand,
                    b.name as brand_name
                FROM package_item pi
                LEFT JOIN product p ON p.bubble_id = pi.product
                LEFT JOIN brand b ON b.bubble_id = p.linked_brand
                WHERE pi.bubble_id = ANY(:item_ids)
                ORDER BY pi.sort NULLS LAST, pi.created_date
            """)
            items = self.db.execute(items_query, {"item_ids": package.linked_package_item}).fetchall()
            result["items"] = [dict(item) for item in items]
        
        return result

    def create_package(
        self,
        name: str,
        price: Optional[Decimal] = None,
        panel: Optional[str] = None,
        panel_qty: Optional[int] = None,
        package_type: Optional[str] = None,
        active: bool = True,
        invoice_desc: Optional[str] = None,
        description: Optional[str] = None,
        max_discount: Optional[int] = None,
        special: bool = False,
        need_approval: bool = False,
        password: Optional[str] = None,
        linked_package_items: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> Package:
        """Create a new package"""
        bubble_id = self._generate_bubble_id()
        now = datetime.now(timezone.utc)
        
        package = Package(
            bubble_id=bubble_id,
            name=name,
            price=price,
            panel=panel,
            panel_qty=panel_qty,
            type=package_type,
            active=active,
            invoice_desc=invoice_desc,
            description=description,
            max_discount=max_discount,
            special=special,
            need_approval=need_approval,
            password=password,
            linked_package_item=linked_package_items or [],
            created_by=created_by,
            created_date=now,
            modified_date=now
        )
        
        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)
        
        return package

    def update_package(
        self,
        bubble_id: str,
        name: Optional[str] = None,
        price: Optional[Decimal] = None,
        panel: Optional[str] = None,
        panel_qty: Optional[int] = None,
        package_type: Optional[str] = None,
        active: Optional[bool] = None,
        invoice_desc: Optional[str] = None,
        description: Optional[str] = None,
        max_discount: Optional[int] = None,
        special: Optional[bool] = None,
        need_approval: Optional[bool] = None,
        password: Optional[str] = None,
        linked_package_items: Optional[List[str]] = None
    ) -> Optional[Package]:
        """Update package"""
        package = self.get_package(bubble_id)
        if not package:
            return None
        
        if name is not None:
            package.name = name
        if price is not None:
            package.price = price
        if panel is not None:
            package.panel = panel
        if panel_qty is not None:
            package.panel_qty = panel_qty
        if package_type is not None:
            package.type = package_type
        if active is not None:
            package.active = active
        if invoice_desc is not None:
            package.invoice_desc = invoice_desc
        if description is not None:
            package.description = description
        if max_discount is not None:
            package.max_discount = max_discount
        if special is not None:
            package.special = special
        if need_approval is not None:
            package.need_approval = need_approval
        if password is not None:
            package.password = password
        if linked_package_items is not None:
            # Ensure it's a list, not None
            package.linked_package_item = linked_package_items if isinstance(linked_package_items, list) else []
        
        package.modified_date = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(package)
        
        return package

    def delete_package(self, bubble_id: str) -> bool:
        """Delete package"""
        package = self.get_package(bubble_id)
        if not package:
            return False
        
        self.db.delete(package)
        self.db.commit()
        return True

    # Package Item methods
    def get_package_item(self, bubble_id: str) -> Optional[PackageItem]:
        """Get package item by bubble_id"""
        return self.db.query(PackageItem).filter(PackageItem.bubble_id == bubble_id).first()

    def create_package_item(
        self,
        product_id: str,
        qty: int,
        total_cost: Optional[int] = None,
        sort: Optional[int] = None,
        created_by: Optional[str] = None
    ) -> PackageItem:
        """Create a new package item"""
        bubble_id = self._generate_bubble_id()
        now = datetime.now(timezone.utc)
        
        item = PackageItem(
            bubble_id=bubble_id,
            product=product_id,
            qty=qty,
            total_cost=total_cost or 0,
            sort=sort or 0,
            created_by=created_by,
            created_date=now,
            modified_date=now
        )
        
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        
        return item

    def update_package_item(
        self,
        bubble_id: str,
        product_id: Optional[str] = None,
        qty: Optional[int] = None,
        total_cost: Optional[int] = None,
        sort: Optional[int] = None
    ) -> Optional[PackageItem]:
        """Update package item"""
        item = self.get_package_item(bubble_id)
        if not item:
            return None
        
        if product_id is not None:
            item.product = product_id
        if qty is not None:
            item.qty = qty
        if total_cost is not None:
            item.total_cost = total_cost
        if sort is not None:
            item.sort = sort
        
        item.modified_date = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(item)
        
        return item

    def delete_package_item(self, bubble_id: str) -> bool:
        """Delete package item"""
        item = self.get_package_item(bubble_id)
        if not item:
            return False
        
        self.db.delete(item)
        self.db.commit()
        return True

    # Product methods
    def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        search: Optional[str] = None,
        brand_id: Optional[str] = None
    ) -> tuple[List[Product], int]:
        """List products with filters"""
        query = self.db.query(Product)
        
        if active_only:
            query = query.filter(Product.active == True)
        
        if brand_id:
            query = query.filter(Product.linked_brand == brand_id)
        
        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.label.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        total = query.count()
        products = query.order_by(Product.created_date.desc().nullslast(), Product.id.desc()).offset(skip).limit(limit).all()
        
        return products, total

    def get_product(self, bubble_id: str) -> Optional[Product]:
        """Get product by bubble_id"""
        return self.db.query(Product).filter(Product.bubble_id == bubble_id).first()

    # Brand methods
    def list_brands(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> tuple[List[Brand], int]:
        """List brands with filters"""
        query = self.db.query(Brand)
        
        if search:
            query = query.filter(Brand.name.ilike(f"%{search}%"))
        
        total = query.count()
        brands = query.order_by(Brand.created_date.desc().nullslast(), Brand.id.desc()).offset(skip).limit(limit).all()
        
        return brands, total

    def get_brand(self, bubble_id: str) -> Optional[Brand]:
        """Get brand by bubble_id"""
        return self.db.query(Brand).filter(Brand.bubble_id == bubble_id).first()


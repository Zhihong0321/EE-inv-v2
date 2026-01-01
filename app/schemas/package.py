from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class PackageItemResponse(BaseModel):
    bubble_id: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    qty: Optional[int] = None
    total_cost: Optional[int] = None
    sort: Optional[int] = None
    inventory: Optional[bool] = None

    class Config:
        from_attributes = True


class PackageItemCreate(BaseModel):
    product_id: str = Field(..., description="Product bubble_id")
    qty: int = Field(..., gt=0, description="Quantity")
    total_cost: Optional[int] = Field(None, ge=0, description="Total cost")
    sort: Optional[int] = Field(0, description="Sort order")


class PackageItemUpdate(BaseModel):
    product_id: Optional[str] = None
    qty: Optional[int] = Field(None, gt=0)
    total_cost: Optional[int] = Field(None, ge=0)
    sort: Optional[int] = None


class PackageCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Package name")
    price: Optional[Decimal] = Field(None, ge=0, description="Package price")
    panel: Optional[str] = Field(None, description="Panel rating/reference")
    panel_qty: Optional[int] = Field(None, ge=0, description="Panel quantity")
    type: Optional[str] = Field(None, description="Package type (e.g., Residential)")
    active: Optional[bool] = Field(True, description="Is package active")
    invoice_desc: Optional[str] = Field(None, description="Invoice description")
    description: Optional[str] = Field(None, description="Package description")
    max_discount: Optional[int] = Field(None, ge=0, le=100, description="Maximum discount percentage")
    special: Optional[bool] = Field(False, description="Is special package")
    need_approval: Optional[bool] = Field(False, description="Needs approval")
    password: Optional[str] = Field(None, description="Package password")
    linked_package_items: Optional[List[str]] = Field(default_factory=list, description="List of package_item bubble_ids")


class PackageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    price: Optional[Decimal] = Field(None, ge=0)
    panel: Optional[str] = None
    panel_qty: Optional[int] = Field(None, ge=0)
    type: Optional[str] = None
    active: Optional[bool] = None
    invoice_desc: Optional[str] = None
    description: Optional[str] = None
    max_discount: Optional[int] = Field(None, ge=0, le=100)
    special: Optional[bool] = None
    need_approval: Optional[bool] = None
    password: Optional[str] = None
    linked_package_items: Optional[List[str]] = None


class PackageImport(BaseModel):
    package_id: str = Field(..., description="The unique bubble_id of the package")
    name: str = Field(..., description="Package name (for reference)")
    price: Decimal = Field(..., ge=0, description="Updated package price")
    invoice_description: Optional[str] = Field(None, description="Updated invoice description")
    internal_description: Optional[str] = Field(None, description="Internal package description")
    items_summary: Optional[str] = Field(None, description="Read-only summary of items")


class PackageResponse(BaseModel):
    id: int
    bubble_id: str
    name: Optional[str] = None
    price: Optional[Decimal] = None
    panel: Optional[str] = None
    panel_qty: Optional[int] = None
    type: Optional[str] = None
    active: Optional[bool] = None
    invoice_desc: Optional[str] = None
    description: Optional[str] = None
    max_discount: Optional[int] = None
    special: Optional[bool] = None
    need_approval: Optional[bool] = None
    password: Optional[str] = None
    linked_package_item: Optional[List[str]] = None
    created_by: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data
    items: List[PackageItemResponse] = []

    class Config:
        from_attributes = True


class PackageListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    packages: List[PackageResponse]


class ProductResponse(BaseModel):
    id: int
    bubble_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    linked_brand: Optional[str] = None
    brand_name: Optional[str] = None
    active: Optional[bool] = None
    image: Optional[str] = None
    label: Optional[str] = None
    solar_output_rating: Optional[int] = None
    inverter_rating: Optional[int] = None
    warranty_name: Optional[str] = None
    warranty_link: Optional[str] = None
    product_warranty_desc: Optional[str] = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    products: List[ProductResponse]


class BrandResponse(BaseModel):
    id: int
    bubble_id: Optional[str] = None
    name: Optional[str] = None
    logo: Optional[str] = None
    created_by: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class BrandListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    brands: List[BrandResponse]



from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class TemplateCreate(BaseModel):
    template_name: str = Field(..., min_length=1, max_length=200)
    company_name: str = Field(..., min_length=1, max_length=200)
    company_address: str = Field(..., min_length=1)
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    sst_registration_no: str = Field(..., min_length=1, pattern=r"^ST\d{10,12}$")
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_account_name: Optional[str] = None
    logo_url: Optional[HttpUrl] = None
    terms_and_conditions: Optional[str] = None
    disclaimer: Optional[str] = None
    is_default: Optional[bool] = False


class TemplateUpdate(BaseModel):
    template_name: Optional[str] = Field(None, min_length=1, max_length=200)
    company_name: Optional[str] = Field(None, min_length=1, max_length=200)
    company_address: Optional[str] = Field(None, min_length=1)
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    sst_registration_no: Optional[str] = Field(None, pattern=r"^ST\d{10,12}$")
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_account_name: Optional[str] = None
    logo_url: Optional[HttpUrl] = None
    terms_and_conditions: Optional[str] = None
    disclaimer: Optional[str] = None
    active: Optional[bool] = None
    is_default: Optional[bool] = None


class TemplateResponse(BaseModel):
    bubble_id: str
    template_name: str
    company_name: str
    company_address: str
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    sst_registration_no: str
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_account_name: Optional[str] = None
    logo_url: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    disclaimer: Optional[str] = None
    active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    templates: list[TemplateResponse]
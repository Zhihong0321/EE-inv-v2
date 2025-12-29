from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplateResponse, TemplateListResponse
from app.repositories.template_repo import TemplateRepository
from app.middleware.auth import get_current_user
from app.models.auth import AuthUser

router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])


from app.utils.helpers import validate_sst_number


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template_data: TemplateCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new invoice template"""
    # Validate SST registration number if provided
    if template_data.sst_registration_no and not validate_sst_number(template_data.sst_registration_no):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid SST registration number format. Expected format: ST followed by 10-12 digits (e.g., ST1234567890)"
        )

    template_repo = TemplateRepository(db)

    # Convert logo_url to string if it's an HttpUrl
    logo_url_str = str(template_data.logo_url) if template_data.logo_url else None

    template = template_repo.create(
        template_name=template_data.template_name,
        company_name=template_data.company_name,
        company_address=template_data.company_address,
        company_phone=template_data.company_phone,
        company_email=template_data.company_email,
        sst_registration_no=template_data.sst_registration_no,
        bank_name=template_data.bank_name,
        bank_account_no=template_data.bank_account_no,
        bank_account_name=template_data.bank_account_name,
        logo_url=logo_url_str,
        terms_and_conditions=template_data.terms_and_conditions,
        disclaimer=template_data.disclaimer,
        apply_sst=template_data.apply_sst,
        is_default=template_data.is_default,
        created_by=current_user.user_id,
    )
    return template


@router.get("/{bubble_id}", response_model=TemplateResponse)
def get_template(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get template by ID"""
    template_repo = TemplateRepository(db)
    template = template_repo.get_by_id(bubble_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return template


@router.get("", response_model=dict)
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: Optional[bool] = True,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all templates"""
    template_repo = TemplateRepository(db)
    templates, total = template_repo.get_all(
        skip=skip,
        limit=limit,
        active_only=active_only,
    )

    return {
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
        "templates": [
            {
                "bubble_id": t.bubble_id,
                "template_name": t.template_name,
                "company_name": t.company_name,
                "company_address": t.company_address,
                "company_phone": t.company_phone,
                "company_email": t.company_email,
                "sst_registration_no": t.sst_registration_no,
                "bank_name": t.bank_name,
                "bank_account_no": t.bank_account_no,
                "bank_account_name": t.bank_account_name,
                "logo_url": t.logo_url,
                "terms_and_conditions": t.terms_and_conditions,
                "disclaimer": t.disclaimer,
                "apply_sst": t.apply_sst,
                "active": t.active,
                "is_default": t.is_default,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in templates
        ],
    }


@router.put("/{bubble_id}", response_model=TemplateResponse)
def update_template(
    bubble_id: str,
    template_data: TemplateUpdate,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update template"""
    # Validate SST registration number if provided
    if template_data.sst_registration_no and not validate_sst_number(template_data.sst_registration_no):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid SST registration number format. Expected format: ST followed by 10-12 digits (e.g., ST1234567890)"
        )

    template_repo = TemplateRepository(db)

    # Convert logo_url to string if it's an HttpUrl
    update_data = template_data.model_dump(exclude_none=True)
    if "logo_url" in update_data and update_data["logo_url"]:
        update_data["logo_url"] = str(update_data["logo_url"])

    template = template_repo.update(bubble_id, **update_data)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return template


@router.delete("/{bubble_id}")
def delete_template(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete template (soft delete)"""
    template_repo = TemplateRepository(db)
    success = template_repo.delete(bubble_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return {"message": "Template deleted successfully"}


@router.post("/{bubble_id}/set-default", response_model=TemplateResponse)
def set_default_template(
    bubble_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set template as default"""
    template_repo = TemplateRepository(db)
    template = template_repo.set_default(bubble_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return template

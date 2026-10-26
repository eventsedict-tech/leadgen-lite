from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.core.database import get_db
from app.models.models import Lead, User, AuditLog
from app.models.enums import CRMStage, LeadPriority, VerificationStatus
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, LeadListResponse
from app.services.deduplication import normalize_company_name, extract_domain, find_existing_lead, check_is_suppressed
from app.api.deps import get_current_user

router = APIRouter(prefix="/leads", tags=["Leads & CRM"])


@router.get("", response_model=LeadListResponse)
def list_leads(
    search: Optional[str] = Query(None, description="Search across company name, email, phone, city"),
    stage: Optional[str] = Query(None, description="Filter by CRM stage"),
    priority: Optional[str] = Query(None, description="Filter by LeadPriority"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    city: Optional[str] = Query(None, description="Filter by city"),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    max_score: Optional[int] = Query(None, ge=0, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Lead).filter(Lead.organization_id == current_user.organization_id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Lead.company_name.ilike(s),
                Lead.general_business_email.ilike(s),
                Lead.public_business_phone.ilike(s),
                Lead.city.ilike(s),
                Lead.industry.ilike(s),
                Lead.publicly_listed_contact_name.ilike(s)
            )
        )

    if stage:
        query = query.filter(Lead.crm_status == stage)
    if priority:
        query = query.filter(Lead.priority == priority)
    if industry:
        query = query.filter(Lead.industry == industry)
    if city:
        query = query.filter(Lead.city == city)
    if min_score is not None:
        query = query.filter(Lead.lead_score >= min_score)
    if max_score is not None:
        query = query.filter(Lead.lead_score <= max_score)

    total = query.count()

    # Sorting
    sort_col = getattr(Lead, sort_by, Lead.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return LeadListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[LeadResponse.model_validate(item) for item in items]
    )


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(
    lead_in: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    domain = extract_domain(lead_in.official_website or lead_in.general_business_email)
    norm_name = normalize_company_name(lead_in.company_name)

    # Check for existing duplicate
    existing = find_existing_lead(db, current_user.organization_id, lead_in.company_name, domain)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A company record already exists for '{existing.company_name}' (ID: {existing.id})."
        )

    # Check suppression list
    is_supp, reason = check_is_suppressed(
        db, current_user.organization_id,
        lead_in.general_business_email,
        lead_in.public_business_phone,
        domain
    )
    initial_crm_status = CRMStage.DO_NOT_CONTACT.value if is_supp else (lead_in.crm_status or CRMStage.NEW.value)

    email_status = VerificationStatus.SOURCE_LISTED.value if lead_in.general_business_email else VerificationStatus.MISSING.value
    phone_status = VerificationStatus.SOURCE_LISTED.value if lead_in.public_business_phone else VerificationStatus.MISSING.value

    new_lead = Lead(
        organization_id=current_user.organization_id,
        company_name=lead_in.company_name.strip(),
        normalized_company_name=norm_name,
        official_website=lead_in.official_website.strip() if lead_in.official_website else None,
        normalized_domain=domain,
        industry=lead_in.industry,
        business_category=lead_in.business_category,
        country=lead_in.country,
        state=lead_in.state,
        city=lead_in.city,
        public_business_address=lead_in.public_business_address,
        public_business_phone=lead_in.public_business_phone,
        general_business_email=lead_in.general_business_email,
        contact_page=lead_in.contact_page,
        publicly_listed_contact_name=lead_in.publicly_listed_contact_name,
        publicly_listed_designation=lead_in.publicly_listed_designation,
        company_linkedin_url=lead_in.company_linkedin_url,
        source_url=lead_in.source_url,
        data_source=lead_in.data_source or "Manual Entry",
        email_verification_status=email_status,
        phone_verification_status=phone_status,
        crm_status=initial_crm_status,
        notes=lead_in.notes,
        tags=lead_in.tags
    )
    db.add(new_lead)
    db.flush()

    # Log audit entry
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="lead_created",
        entity_type="lead",
        entity_id=new_lead.id,
        details_json=f'{{"company_name": "{new_lead.company_name}", "data_source": "{new_lead.data_source}"}}'
    )
    db.add(audit)
    db.commit()
    db.refresh(new_lead)

    return LeadResponse.model_validate(new_lead)


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadResponse.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: int,
    lead_in: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_dict = lead_in.model_dump(exclude_unset=True)

    if "company_name" in update_dict and update_dict["company_name"]:
        lead.company_name = update_dict["company_name"].strip()
        lead.normalized_company_name = normalize_company_name(lead.company_name)

    if "official_website" in update_dict:
        lead.official_website = update_dict["official_website"]
        lead.normalized_domain = extract_domain(lead.official_website or lead.general_business_email)

    for field, value in update_dict.items():
        if field not in ("company_name", "official_website"):
            setattr(lead, field, value)

    # Log audit
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="lead_updated",
        entity_type="lead",
        entity_id=lead.id,
        details_json=f'{{"updated_fields": {list(update_dict.keys())}}}'
    )
    db.add(audit)
    db.commit()
    db.refresh(lead)

    return LeadResponse.model_validate(lead)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(lead)
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="lead_deleted",
        entity_type="lead",
        entity_id=lead_id,
        details_json=f'{{"company_name": "{lead.company_name}"}}'
    )
    db.add(audit)
    db.commit()
    return None

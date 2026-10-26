from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.enums import CRMStage, LeadPriority, VerificationStatus


class LeadBase(BaseModel):
    company_name: str
    official_website: Optional[str] = None
    industry: Optional[str] = None
    business_category: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    public_business_address: Optional[str] = None
    public_business_phone: Optional[str] = None
    general_business_email: Optional[str] = None
    contact_page: Optional[str] = None
    publicly_listed_contact_name: Optional[str] = None
    publicly_listed_designation: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    source_url: Optional[str] = None
    data_source: Optional[str] = "Manual Entry"
    notes: Optional[str] = None
    tags: Optional[str] = None


class LeadCreate(LeadBase):
    crm_status: Optional[str] = CRMStage.NEW.value


class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    official_website: Optional[str] = None
    industry: Optional[str] = None
    business_category: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    public_business_address: Optional[str] = None
    public_business_phone: Optional[str] = None
    general_business_email: Optional[str] = None
    contact_page: Optional[str] = None
    publicly_listed_contact_name: Optional[str] = None
    publicly_listed_designation: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    crm_status: Optional[str] = None
    lead_score: Optional[int] = None
    priority: Optional[str] = None
    marketing_opportunity: Optional[str] = None
    recommended_service: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[str] = None
    email_verification_status: Optional[str] = None
    phone_verification_status: Optional[str] = None


class LeadResponse(LeadBase):
    id: int
    organization_id: int
    normalized_company_name: str
    normalized_domain: Optional[str] = None
    research_date: Optional[datetime] = None
    last_verified_date: Optional[datetime] = None
    website_status: Optional[str] = None
    email_verification_status: str
    phone_verification_status: str
    lead_score: int
    priority: str
    marketing_opportunity: Optional[str] = None
    recommended_service: Optional[str] = None
    crm_status: str
    follow_up_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[LeadResponse]

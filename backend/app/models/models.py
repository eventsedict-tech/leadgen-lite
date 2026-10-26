import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import (
    CRMStage, LeadPriority, VerificationStatus,
    OutreachChannel, OutreachLanguage, CampaignStatus,
    RecipientStatus, TaskStatus, UserRole
)


def get_utc_now():
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=get_utc_now)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.MEMBER.value, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_utc_now)

    organization = relationship("Organization", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Core company identification
    company_name = Column(String(255), nullable=False, index=True)
    normalized_company_name = Column(String(255), nullable=False, index=True)
    official_website = Column(String(500), nullable=True)
    normalized_domain = Column(String(255), nullable=True, index=True)
    
    # Categorization
    industry = Column(String(150), nullable=True, index=True)
    business_category = Column(String(150), nullable=True)
    
    # Location
    country = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    public_business_address = Column(Text, nullable=True)
    
    # Contact Information
    public_business_phone = Column(String(100), nullable=True)
    general_business_email = Column(String(255), nullable=True, index=True)
    contact_page = Column(String(500), nullable=True)
    publicly_listed_contact_name = Column(String(255), nullable=True)
    publicly_listed_designation = Column(String(255), nullable=True)
    company_linkedin_url = Column(String(500), nullable=True)
    
    # Sourcing & Research
    source_url = Column(String(500), nullable=True)
    data_source = Column(String(100), nullable=True, default="Manual / File Import")
    research_date = Column(DateTime, nullable=True)
    last_verified_date = Column(DateTime, nullable=True)
    website_status = Column(String(50), nullable=True, default="Pending")
    
    # Verification statuses (Distinguishes Verified, Source-listed, Inferred, Missing, Conflicting)
    email_verification_status = Column(String(50), default=VerificationStatus.MISSING.value)
    phone_verification_status = Column(String(50), default=VerificationStatus.MISSING.value)
    
    # Marketing Intelligence & Scoring
    lead_score = Column(Integer, default=0, index=True)
    priority = Column(String(50), default=LeadPriority.REVIEW.value, index=True)
    marketing_opportunity = Column(Text, nullable=True)
    recommended_service = Column(String(255), nullable=True)
    
    # CRM Management
    crm_status = Column(String(50), default=CRMStage.NEW.value, index=True)
    follow_up_date = Column(DateTime, nullable=True, index=True)
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON-encoded array of tags
    
    created_at = Column(DateTime, default=get_utc_now, index=True)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    # Relationships
    organization = relationship("Organization", back_populates="leads")
    sources = relationship("LeadSource", back_populates="lead", cascade="all, delete-orphan")
    audits = relationship("WebsiteAudit", back_populates="lead", cascade="all, delete-orphan")
    scores = relationship("LeadScore", back_populates="lead", cascade="all, delete-orphan")
    outreach_drafts = relationship("OutreachDraft", back_populates="lead", cascade="all, delete-orphan")
    follow_up_tasks = relationship("FollowUpTask", back_populates="lead", cascade="all, delete-orphan")
    research_jobs = relationship("ResearchJob", back_populates="lead", cascade="all, delete-orphan")
    campaign_recipients = relationship("CampaignRecipient", back_populates="lead", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_org_domain", "organization_id", "normalized_domain"),
        Index("idx_org_company", "organization_id", "normalized_company_name"),
        Index("idx_org_stage", "organization_id", "crm_status"),
        Index("idx_org_score", "organization_id", "lead_score"),
    )


class LeadSource(Base):
    __tablename__ = "lead_sources"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    source_name = Column(String(100), nullable=False)
    source_type = Column(String(50), nullable=False)  # csv_import, google_places, search_api, manual
    raw_payload = Column(Text, nullable=True)  # JSON string of original source data
    created_at = Column(DateTime, default=get_utc_now)

    lead = relationship("Lead", back_populates="sources")


class WebsiteAudit(Base):
    __tablename__ = "website_audits"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    audited_url = Column(String(500), nullable=False)
    
    # Audit Results
    http_status = Column(Integer, nullable=True)
    is_https = Column(Boolean, default=False)
    page_title = Column(String(500), nullable=True)
    meta_description = Column(Text, nullable=True)
    h1_heading = Column(Text, nullable=True)
    images_missing_alt_count = Column(Integer, default=0)
    total_images_count = Column(Integer, default=0)
    has_viewport = Column(Boolean, default=False)
    has_robots_txt = Column(Boolean, default=False)
    has_sitemap_xml = Column(Boolean, default=False)
    has_contact_page = Column(Boolean, default=False)
    internal_links_count = Column(Integer, default=0)
    local_seo_indicators = Column(Text, nullable=True)
    
    findings_json = Column(Text, nullable=True)  # List of {finding, evidence, impact, recommendation, service}
    overall_assessment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    lead = relationship("Lead", back_populates="audits")


class LeadScore(Base):
    __tablename__ = "lead_scores"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    
    total_score = Column(Integer, nullable=False)
    priority_tier = Column(String(50), nullable=False)
    industry_fit_score = Column(Float, default=0.0)
    website_opportunity_score = Column(Float, default=0.0)
    info_quality_score = Column(Float, default=0.0)
    marketing_opportunity_score = Column(Float, default=0.0)
    business_relevance_score = Column(Float, default=0.0)
    
    breakdown_json = Column(Text, nullable=True)
    manual_override = Column(Boolean, default=False)
    override_reason = Column(Text, nullable=True)
    scored_by = Column(String(100), default="Algorithm")
    created_at = Column(DateTime, default=get_utc_now)

    lead = relationship("Lead", back_populates="scores")


class OutreachDraft(Base):
    __tablename__ = "outreach_drafts"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    
    channel = Column(String(50), nullable=False)  # cold_email, follow_up_email, linkedin_note, etc.
    language = Column(String(10), default=OutreachLanguage.EN.value)  # en, hi
    subject_line = Column(String(255), nullable=True)
    message_body = Column(Text, nullable=False)
    recommended_service = Column(String(255), nullable=True)
    personalization_evidence = Column(Text, nullable=True)
    suggested_next_action = Column(String(255), nullable=True)
    
    is_approved = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now)

    lead = relationship("Lead", back_populates="outreach_drafts")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    channel = Column(String(50), default=OutreachChannel.COLD_EMAIL.value)
    status = Column(String(50), default=CampaignStatus.DRAFT.value)
    sending_limit_per_day = Column(Integer, default=50)
    created_at = Column(DateTime, default=get_utc_now)

    recipients = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")


class CampaignRecipient(Base):
    __tablename__ = "campaign_recipients"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    outreach_draft_id = Column(Integer, ForeignKey("outreach_drafts.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(String(50), default=RecipientStatus.PENDING.value)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    campaign = relationship("Campaign", back_populates="recipients")
    lead = relationship("Lead", back_populates="campaign_recipients")


class FollowUpTask(Base):
    __tablename__ = "follow_up_tasks"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(255), nullable=False)
    due_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), default=TaskStatus.PENDING.value)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    lead = relationship("Lead", back_populates="follow_up_tasks")


class SuppressionList(Base):
    __tablename__ = "suppression_list"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(100), nullable=True, index=True)
    domain = Column(String(255), nullable=True, index=True)
    reason = Column(String(255), nullable=False, default="Requested Unsubscribe")
    added_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)


class ProviderIntegration(Base):
    __tablename__ = "provider_integrations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    provider_type = Column(String(100), nullable=False)  # google_places, search_api, pagespeed, openai, smtp, whatsapp
    is_active = Column(Boolean, default=False)
    config_json = Column(Text, nullable=True)  # Securely stored credentials/settings
    created_at = Column(DateTime, default=get_utc_now)


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    total_records = Column(Integer, default=0)
    imported_records = Column(Integer, default=0)
    skipped_records = Column(Integer, default=0)
    merged_records = Column(Integer, default=0)
    error_report_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)


class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="queued")  # queued, in_progress, completed, failed
    log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    lead = relationship("Lead", back_populates="research_jobs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # lead_created, lead_updated, score_overridden, etc.
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    user = relationship("User", back_populates="audit_logs")

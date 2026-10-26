import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.models import Lead, WebsiteAudit, ResearchJob, AuditLog
from app.models.enums import VerificationStatus
from app.services.seo_auditor import perform_seo_audit
from app.services.deduplication import extract_domain


async def enrich_lead(db: Session, org_id: int, user_id: int, lead_id: int) -> Dict[str, Any]:
    """
    Enriches a company record with verified/source-listed information from public website analysis.
    Maintains strict verification states (SOURCE_LISTED, not auto-VERIFIED).
    Never fabricates contact details.
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == org_id
    ).first()
    if not lead:
        raise ValueError(f"Lead ID {lead_id} not found")

    # Update or create research job
    research_job = db.query(ResearchJob).filter(
        ResearchJob.lead_id == lead.id,
        ResearchJob.organization_id == org_id
    ).first()
    if not research_job:
        research_job = ResearchJob(
            organization_id=org_id,
            lead_id=lead.id,
            status="in_progress",
            log="Initiating website analysis and contact enrichment..."
        )
        db.add(research_job)
        db.flush()
    else:
        research_job.status = "in_progress"
        research_job.log = "Research in progress..."
        db.flush()

    target_url = lead.official_website
    now = datetime.now(timezone.utc)

    if not target_url:
        lead.website_status = "Missing Website"
        lead.marketing_opportunity = "No official website found online. High-value opportunity for custom website design and online presence setup."
        lead.recommended_service = "Web Design & Online Brand Launch"
        lead.research_date = now
        lead.last_verified_date = now
        research_job.status = "completed"
        research_job.log = "Completed: No website listed on company record."
        db.commit()
        return {"status": "completed", "message": "No website listed"}

    # Run SEO Audit & Crawl with SSRF protection
    audit_data = await perform_seo_audit(target_url)

    # Save WebsiteAudit record
    audit_record = WebsiteAudit(
        organization_id=org_id,
        lead_id=lead.id,
        audited_url=audit_data["audited_url"],
        http_status=audit_data["http_status"],
        is_https=audit_data["is_https"],
        page_title=audit_data["page_title"],
        meta_description=audit_data["meta_description"],
        h1_heading=audit_data["h1_heading"],
        images_missing_alt_count=audit_data["images_missing_alt_count"],
        total_images_count=audit_data["total_images_count"],
        has_viewport=audit_data["has_viewport"],
        has_robots_txt=audit_data["has_robots_txt"],
        has_sitemap_xml=audit_data["has_sitemap_xml"],
        has_contact_page=audit_data["has_contact_page"],
        internal_links_count=audit_data["internal_links_count"],
        local_seo_indicators=audit_data["local_seo_indicators"],
        findings_json=json.dumps([f.model_dump() for f in audit_data["findings"]]),
        overall_assessment=audit_data["overall_assessment"]
    )
    db.add(audit_record)

    # Update Lead attributes
    lead.research_date = now
    lead.last_verified_date = now
    lead.website_status = "Active" if audit_data["http_status"] == 200 else f"HTTP {audit_data['http_status']}"
    lead.marketing_opportunity = ", ".join(audit_data["opportunities"]) if audit_data["opportunities"] else "Growth Marketing"
    lead.recommended_service = audit_data["primary_recommended_service"]

    # Enrich missing contact details found on public website strictly as SOURCE_LISTED
    contacts = audit_data.get("extracted_contacts", {})
    new_phone = contacts.get("phone")
    new_email = contacts.get("email")
    socials = contacts.get("socials", {})

    if new_phone and not lead.public_business_phone:
        lead.public_business_phone = new_phone
        lead.phone_verification_status = VerificationStatus.SOURCE_LISTED.value

    if new_email and not lead.general_business_email:
        lead.general_business_email = new_email
        lead.email_verification_status = VerificationStatus.SOURCE_LISTED.value

    if socials.get("linkedin") and not lead.company_linkedin_url:
        lead.company_linkedin_url = socials["linkedin"]

    research_job.status = "completed"
    research_job.log = f"Successfully audited website and enriched opportunities. Primary service: {lead.recommended_service}"

    # Log audit
    audit_log = AuditLog(
        organization_id=org_id,
        user_id=user_id,
        action="lead_enriched",
        entity_type="lead",
        entity_id=lead.id,
        details_json=json.dumps({
            "website_status": lead.website_status,
            "recommended_service": lead.recommended_service,
            "opportunities_found": len(audit_data["opportunities"])
        })
    )
    db.add(audit_log)
    db.commit()

    return {
        "status": "completed",
        "audit_id": audit_record.id,
        "lead_id": lead.id,
        "recommended_service": lead.recommended_service,
        "opportunities": audit_data["opportunities"]
    }

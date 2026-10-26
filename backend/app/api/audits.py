import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, Lead, WebsiteAudit, AuditLog
from app.schemas.audit import WebsiteAuditResponse, RunAuditRequest, SEOFinding
from app.services.seo_auditor import perform_seo_audit
from app.api.deps import get_current_user

router = APIRouter(prefix="/audits", tags=["Website SEO Audits"])


@router.post("/run", response_model=WebsiteAuditResponse)
async def run_audit(
    req: RunAuditRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_url = None
    lead = None

    if req.lead_id:
        lead = db.query(Lead).filter(
            Lead.id == req.lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        target_url = lead.official_website
        if not target_url:
            raise HTTPException(status_code=400, detail="Lead does not have an official website listed.")
    elif req.url:
        target_url = req.url
    else:
        raise HTTPException(status_code=400, detail="Must provide either lead_id or url")

    audit_data = await perform_seo_audit(target_url)

    # If associated with lead, link lead_id
    lead_id = lead.id if lead else (req.lead_id or 0)
    
    findings_dicts = [f.model_dump() for f in audit_data["findings"]]

    audit_record = WebsiteAudit(
        organization_id=current_user.organization_id,
        lead_id=lead_id,
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
        findings_json=json.dumps(findings_dicts),
        overall_assessment=audit_data["overall_assessment"]
    )
    db.add(audit_record)

    if lead:
        lead.website_status = "Active" if audit_data["http_status"] == 200 else f"HTTP {audit_data['http_status']}"
        lead.marketing_opportunity = ", ".join(audit_data["opportunities"]) if audit_data["opportunities"] else "Growth Retainer"
        lead.recommended_service = audit_data["primary_recommended_service"]

    db.commit()
    db.refresh(audit_record)

    return WebsiteAuditResponse(
        id=audit_record.id,
        lead_id=audit_record.lead_id,
        audited_url=audit_record.audited_url,
        http_status=audit_record.http_status,
        is_https=audit_record.is_https,
        page_title=audit_record.page_title,
        meta_description=audit_record.meta_description,
        h1_heading=audit_record.h1_heading,
        images_missing_alt_count=audit_record.images_missing_alt_count,
        total_images_count=audit_record.total_images_count,
        has_viewport=audit_record.has_viewport,
        has_robots_txt=audit_record.has_robots_txt,
        has_sitemap_xml=audit_record.has_sitemap_xml,
        has_contact_page=audit_record.has_contact_page,
        internal_links_count=audit_record.internal_links_count,
        local_seo_indicators=audit_record.local_seo_indicators,
        findings=[SEOFinding(**f) for f in findings_dicts],
        overall_assessment=audit_record.overall_assessment,
        created_at=audit_record.created_at
    )


@router.get("/lead/{lead_id}", response_model=List[WebsiteAuditResponse])
def get_lead_audits(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    audits = db.query(WebsiteAudit).filter(
        WebsiteAudit.lead_id == lead_id,
        WebsiteAudit.organization_id == current_user.organization_id
    ).order_by(WebsiteAudit.created_at.desc()).all()

    resp = []
    for a in audits:
        raw_findings = json.loads(a.findings_json) if a.findings_json else []
        resp.append(WebsiteAuditResponse(
            id=a.id,
            lead_id=a.lead_id,
            audited_url=a.audited_url,
            http_status=a.http_status,
            is_https=a.is_https,
            page_title=a.page_title,
            meta_description=a.meta_description,
            h1_heading=a.h1_heading,
            images_missing_alt_count=a.images_missing_alt_count,
            total_images_count=a.total_images_count,
            has_viewport=a.has_viewport,
            has_robots_txt=a.has_robots_txt,
            has_sitemap_xml=a.has_sitemap_xml,
            has_contact_page=a.has_contact_page,
            internal_links_count=a.internal_links_count,
            local_seo_indicators=a.local_seo_indicators,
            findings=[SEOFinding(**f) for f in raw_findings],
            overall_assessment=a.overall_assessment,
            created_at=a.created_at
        ))
    return resp

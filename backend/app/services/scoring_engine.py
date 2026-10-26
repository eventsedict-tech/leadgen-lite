import json
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.models import Lead, WebsiteAudit, LeadScore, AuditLog
from app.models.enums import LeadPriority
from app.schemas.scoring import ScoringWeights, ScoreItem, ScoreCalculationResponse

# High-converting commercial B2B & local service industries
HIGH_VALUE_INDUSTRIES = {
    "healthcare", "dental", "legal", "law", "attorney", "real estate", "construction",
    "home services", "plumbing", "roofing", "hvac", "solar", "clean energy", "finance",
    "accounting", "b2b", "manufacturing", "technology", "consulting", "logistics"
}


def calculate_lead_score(
    lead: Lead,
    audit: Optional[WebsiteAudit] = None,
    weights: Optional[ScoringWeights] = None
) -> ScoreCalculationResponse:
    """
    Computes an explainable lead score between 0 and 100 based on:
    - Industry fit
    - Website opportunities (from real audit)
    - Business contact quality
    - Specific marketing opportunity
    - Business relevance
    """
    if weights is None:
        weights = ScoringWeights()

    breakdown: List[ScoreItem] = []
    opportunities: List[str] = []

    # 1. Industry Fit (Default weight: 25)
    industry_str = (lead.industry or lead.business_category or "").lower()
    if any(ind in industry_str for ind in HIGH_VALUE_INDUSTRIES):
        ind_score = weights.industry_fit
        ind_exp = f"Industry '{lead.industry}' is a high-intent commercial sector with active marketing spend."
    elif lead.industry:
        ind_score = weights.industry_fit * 0.6
        ind_exp = f"Industry '{lead.industry}' has moderate commercial demand for digital services."
    else:
        ind_score = weights.industry_fit * 0.2
        ind_exp = "Industry not explicitly specified; lower baseline industry fit."
    
    breakdown.append(ScoreItem(
        category="Industry Fit",
        earned_score=round(ind_score, 1),
        max_score=weights.industry_fit,
        explanation=ind_exp
    ))

    # 2. Website Opportunities (Default weight: 25)
    # Higher score when there are actionable gaps to pitch!
    web_score = 0.0
    if not lead.official_website:
        web_score = weights.website_opportunities  # Complete lack of website is highest pitch opportunity
        web_exp = "No official website listed; prime prospect for complete web design and digital launch."
        opportunities.append("Missing Website")
    elif audit:
        # Check audit findings
        audit_opps = 0
        if not audit.is_https:
            audit_opps += 1
            opportunities.append("Insecure HTTP")
        if not audit.has_viewport:
            audit_opps += 1
            opportunities.append("Missing Mobile Viewport")
        if not audit.page_title:
            audit_opps += 1
            opportunities.append("Missing Page Title")
        if not audit.meta_description:
            audit_opps += 1
            opportunities.append("Missing Meta Description")
        if not audit.h1_heading:
            audit_opps += 1
            opportunities.append("Missing H1 Tag")
        if audit.images_missing_alt_count > 0:
            audit_opps += 1
            opportunities.append("Images Missing Alt Text")
        if not audit.has_contact_page:
            audit_opps += 1
            opportunities.append("No Contact Page")
        if not audit.has_sitemap_xml:
            audit_opps += 1
            opportunities.append("Missing XML Sitemap")
        
        ratio = min(audit_opps / 4.0, 1.0)
        web_score = round(weights.website_opportunities * (0.3 + 0.7 * ratio), 1)
        web_exp = f"Identified {audit_opps} specific technical SEO and conversion opportunities on audited website."
    else:
        web_score = round(weights.website_opportunities * 0.4, 1)
        web_exp = "Website is present but has not undergone full technical audit yet."

    breakdown.append(ScoreItem(
        category="Website Opportunities",
        earned_score=round(web_score, 1),
        max_score=weights.website_opportunities,
        explanation=web_exp
    ))

    # 3. Business Information Quality (Default weight: 15)
    info_points = 0.0
    info_reasons = []
    if lead.public_business_phone:
        info_points += 0.35
        info_reasons.append("verified phone")
    if lead.general_business_email:
        info_points += 0.35
        info_reasons.append("contact email")
    if lead.publicly_listed_contact_name:
        info_points += 0.20
        info_reasons.append("decision maker name")
    if lead.company_linkedin_url:
        info_points += 0.10
        info_reasons.append("LinkedIn profile")
    
    info_score = round(weights.business_info_quality * info_points, 1)
    info_exp = f"Contact availability: {', '.join(info_reasons)}" if info_reasons else "Minimal contact details available."
    breakdown.append(ScoreItem(
        category="Business Info Quality",
        earned_score=round(info_score, 1),
        max_score=weights.business_info_quality,
        explanation=info_exp
    ))

    # 4. Specific Marketing Opportunity (Default weight: 20)
    mktg_score = 0.0
    if not lead.official_website:
        mktg_score = weights.specific_marketing_opportunity
        mktg_exp = "Urgent need for web presence development."
        primary_service = "Web Design & Online Brand Launch"
    elif audit and (not audit.has_viewport or not audit.is_https):
        mktg_score = weights.specific_marketing_opportunity * 0.95
        mktg_exp = "Critical technical deficiencies (Mobile Responsiveness or SSL Security)."
        primary_service = "Responsive Web Redesign & SSL Security"
    elif audit and (not audit.page_title or not audit.meta_description):
        mktg_score = weights.specific_marketing_opportunity * 0.85
        mktg_exp = "High SEO gap: lacking core search engine meta tags."
        primary_service = "On-Page SEO Optimization"
    elif audit and not audit.has_contact_page:
        mktg_score = weights.specific_marketing_opportunity * 0.75
        mktg_exp = "Conversion gap: website lacks direct contact call-to-actions."
        primary_service = "Conversion Rate Optimization (CRO)"
    else:
        mktg_score = weights.specific_marketing_opportunity * 0.5
        mktg_exp = "Standard digital growth retainer and local visibility enhancement."
        primary_service = lead.recommended_service or "Digital Marketing Growth Retainer"

    breakdown.append(ScoreItem(
        category="Specific Marketing Opportunity",
        earned_score=round(mktg_score, 1),
        max_score=weights.specific_marketing_opportunity,
        explanation=mktg_exp
    ))

    # 5. Business Relevance (Default weight: 15)
    rel_points = 0.0
    rel_reasons = []
    if lead.city:
        rel_points += 0.4
        rel_reasons.append(f"targeted city ({lead.city})")
    if lead.country:
        rel_points += 0.3
        rel_reasons.append(f"country ({lead.country})")
    if lead.source_url:
        rel_points += 0.3
        rel_reasons.append("verifiable source listing")
    
    rel_score = round(weights.business_relevance * min(rel_points, 1.0), 1)
    rel_exp = f"Relevance factors: {', '.join(rel_reasons)}" if rel_reasons else "Low geographic targeting data."
    breakdown.append(ScoreItem(
        category="Business Relevance",
        earned_score=round(rel_score, 1),
        max_score=weights.business_relevance,
        explanation=rel_exp
    ))

    # Total Calculation
    total = int(round(sum(item.earned_score for item in breakdown)))
    total = max(0, min(100, total))

    # Priority Tier assignment:
    # 80–100: High Priority
    # 60–79: Medium Priority
    # 40–59: Low Priority
    # 0–39: Review Required
    if total >= 80:
        priority_tier = LeadPriority.HIGH.value
    elif total >= 60:
        priority_tier = LeadPriority.MEDIUM.value
    elif total >= 40:
        priority_tier = LeadPriority.LOW.value
    else:
        priority_tier = LeadPriority.REVIEW.value

    return ScoreCalculationResponse(
        total_score=total,
        priority_tier=priority_tier,
        breakdown=breakdown,
        marketing_opportunities=opportunities,
        recommended_service=primary_service
    )


def save_lead_score(
    db: Session,
    org_id: int,
    lead: Lead,
    score_res: ScoreCalculationResponse,
    scored_by: str = "Algorithm",
    manual_override: bool = False,
    override_reason: Optional[str] = None
) -> LeadScore:
    """Persists score breakdown to database and synchronizes lead attributes."""
    bd_dict = {item.category: item.earned_score for item in score_res.breakdown}

    score_rec = LeadScore(
        organization_id=org_id,
        lead_id=lead.id,
        total_score=score_res.total_score,
        priority_tier=score_res.priority_tier,
        industry_fit_score=bd_dict.get("Industry Fit", 0.0),
        website_opportunity_score=bd_dict.get("Website Opportunities", 0.0),
        info_quality_score=bd_dict.get("Business Info Quality", 0.0),
        marketing_opportunity_score=bd_dict.get("Specific Marketing Opportunity", 0.0),
        business_relevance_score=bd_dict.get("Business Relevance", 0.0),
        breakdown_json=json.dumps([item.model_dump() for item in score_res.breakdown]),
        manual_override=manual_override,
        override_reason=override_reason,
        scored_by=scored_by
    )
    db.add(score_rec)

    # Sync lead
    lead.lead_score = score_res.total_score
    lead.priority = score_res.priority_tier
    if score_res.recommended_service:
        lead.recommended_service = score_res.recommended_service
    if score_res.marketing_opportunities:
        lead.marketing_opportunity = ", ".join(score_res.marketing_opportunities)

    db.commit()
    db.refresh(score_rec)
    return score_rec

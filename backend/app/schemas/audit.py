from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class SEOFinding(BaseModel):
    category: str
    finding: str
    evidence: str
    impact: str
    recommended_improvement: str
    suggested_service: str
    passed: bool


class WebsiteAuditResponse(BaseModel):
    id: int
    lead_id: int
    audited_url: str
    http_status: Optional[int]
    is_https: bool
    page_title: Optional[str]
    meta_description: Optional[str]
    h1_heading: Optional[str]
    images_missing_alt_count: int
    total_images_count: int
    has_viewport: bool
    has_robots_txt: bool
    has_sitemap_xml: bool
    has_contact_page: bool
    internal_links_count: int
    local_seo_indicators: Optional[str]
    findings: List[SEOFinding]
    overall_assessment: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RunAuditRequest(BaseModel):
    lead_id: Optional[int] = None
    url: Optional[str] = None

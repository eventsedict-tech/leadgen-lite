import re
from urllib.parse import urlparse
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.models import Lead, SuppressionList

# Common company suffixes to strip during normalization
SUFFIXES_PATTERN = re.compile(
    r"\b(inc|incorporated|corp|corporation|llc|llp|ltd|limited|pvt|private|gmbh|co|company|group|services|enterprises)\b",
    re.IGNORECASE
)

# Common free webmail domains that should NOT be used for domain-based company deduplication
GENERIC_MAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
    "aol.com", "protonmail.com", "zoho.com", "mail.com", "yandex.com"
}


def normalize_company_name(name: Optional[str]) -> str:
    """Normalizes company name for deduplication matching."""
    if not name:
        return ""
    text = name.lower().strip()
    # Remove characters other than alphanumeric and spaces
    text = re.sub(r"[^\w\s]", " ", text)
    # Remove legal suffixes
    text = SUFFIXES_PATTERN.sub(" ", text)
    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_domain(url_or_email: Optional[str]) -> Optional[str]:
    """Extracts cleaned base domain from a URL or email address."""
    if not url_or_email:
        return None
    val = url_or_email.strip().lower()
    
    # If it's an email address
    if "@" in val:
        parts = val.split("@")
        if len(parts) == 2:
            domain = parts[1].strip()
            if domain not in GENERIC_MAIL_DOMAINS:
                return domain
            return None

    # Prepend http:// if scheme is missing so urlparse works properly
    if not val.startswith(("http://", "https://")):
        val = "http://" + val

    try:
        parsed = urlparse(val)
        domain = parsed.netloc or parsed.path
        # Remove port if present
        domain = domain.split(":")[0]
        # Remove www.
        if domain.startswith("www."):
            domain = domain[4:]
        return domain if "." in domain else None
    except Exception:
        return None


def find_existing_lead(
    db: Session,
    org_id: int,
    company_name: str,
    domain: Optional[str] = None
) -> Optional[Lead]:
    """
    Checks if a lead already exists in this organization.
    Prioritizes domain match (if not generic), then falls back to normalized company name.
    """
    if domain and domain not in GENERIC_MAIL_DOMAINS:
        lead_by_domain = db.query(Lead).filter(
            Lead.organization_id == org_id,
            Lead.normalized_domain == domain
        ).first()
        if lead_by_domain:
            return lead_by_domain

    norm_name = normalize_company_name(company_name)
    if norm_name:
        lead_by_name = db.query(Lead).filter(
            Lead.organization_id == org_id,
            Lead.normalized_company_name == norm_name
        ).first()
        if lead_by_name:
            return lead_by_name

    return None


def check_is_suppressed(
    db: Session,
    org_id: int,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    domain: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Checks if contact details exist in the organization's suppression list.
    Returns (is_suppressed, reason).
    """
    query = db.query(SuppressionList).filter(SuppressionList.organization_id == org_id)

    if email:
        match = query.filter(SuppressionList.email == email.strip().lower()).first()
        if match:
            return True, f"Email suppressed: {match.reason}"

    if phone:
        # Normalize digits
        clean_phone = re.sub(r"\D", "", phone)
        if clean_phone:
            match = query.filter(SuppressionList.phone == clean_phone).first()
            if match:
                return True, f"Phone suppressed: {match.reason}"

    if domain:
        clean_domain = domain.strip().lower()
        match = query.filter(SuppressionList.domain == clean_domain).first()
        if match:
            return True, f"Domain suppressed: {match.reason}"

    return False, None

import re
import json
from urllib.parse import urlparse, urljoin
from typing import Dict, Any, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup
from app.core.ssrf import validate_url_for_ssrf
from app.schemas.audit import SEOFinding

# Maximum response size: 2 Megabytes
MAX_BODY_BYTES = 2 * 1024 * 1024
DEFAULT_TIMEOUT_SEC = 5.0
USER_AGENT = "LeadGenLite-Auditor/1.0 (Public SEO Evaluation Bot; +https://leadgenlite.local/bot)"


async def safe_fetch_page(url: str, max_redirects: int = 3) -> Tuple[bool, Optional[str], Optional[int], Optional[str], str]:
    """
    Safely fetches a web page with strict SSRF protection, redirect verification,
    timeout limits, and response body size limits.
    Returns: (success, html_text, status_code, error_message, final_url)
    """
    current_url = url.strip()
    if not current_url.startswith(("http://", "https://")):
        current_url = "https://" + current_url

    redirect_count = 0
    final_url = current_url

    while redirect_count <= max_redirects:
        is_safe, error_msg, _ = validate_url_for_ssrf(current_url)
        if not is_safe:
            return False, None, None, f"Security block (SSRF Guard): {error_msg}", current_url

        try:
            async with httpx.AsyncClient(
                timeout=DEFAULT_TIMEOUT_SEC,
                headers={"User-Agent": USER_AGENT},
                follow_redirects=False
            ) as client:
                resp = await client.get(current_url)

                # Handle redirects manually to validate each target URL against SSRF
                if resp.is_redirect:
                    redirect_count += 1
                    loc = resp.headers.get("Location")
                    if not loc:
                        return False, None, resp.status_code, "Redirect with empty Location header", current_url
                    current_url = urljoin(current_url, loc)
                    continue

                status_code = resp.status_code
                content = resp.content
                if len(content) > MAX_BODY_BYTES:
                    content = content[:MAX_BODY_BYTES]

                # Decode HTML with fallbacks
                try:
                    html_text = content.decode(resp.encoding or "utf-8", errors="replace")
                except Exception:
                    html_text = content.decode("utf-8", errors="replace")

                return True, html_text, status_code, None, current_url

        except httpx.TimeoutException:
            return False, None, None, "Connection timed out after 5 seconds", current_url
        except httpx.ConnectError as e:
            return False, None, None, f"Connection failed: {str(e)}", current_url
        except Exception as e:
            return False, None, None, f"Fetch error: {str(e)}", current_url

    return False, None, None, "Too many redirects encountered", current_url


async def check_url_exists(base_url: str, path: str) -> bool:
    """Safely checks if a sub-resource like /robots.txt or /sitemap.xml exists."""
    target_url = urljoin(base_url, path)
    is_safe, _, _ = validate_url_for_ssrf(target_url)
    if not is_safe:
        return False
    try:
        async with httpx.AsyncClient(
            timeout=3.0,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=False
        ) as client:
            resp = await client.head(target_url)
            if resp.status_code == 200:
                return True
            # Fallback to GET with small byte range if HEAD returned 405
            if resp.status_code in (403, 405):
                resp_get = await client.get(target_url, headers={"Range": "bytes=0-100"})
                return resp_get.status_code in (200, 206)
            return False
    except Exception:
        return False


def extract_social_links(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    """Finds links to social media profiles."""
    social_platforms = {
        "linkedin": r"linkedin\.com/(company|in)/",
        "facebook": r"facebook\.com/",
        "instagram": r"instagram\.com/",
        "twitter": r"(twitter\.com|x\.com)/",
        "youtube": r"youtube\.com/"
    }
    found = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        for platform, pattern in social_platforms.items():
            if platform not in found and re.search(pattern, href, re.IGNORECASE):
                found[platform] = href
    return found


def extract_contact_info_from_html(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    """Extracts public contact information found on the page."""
    phone = None
    email = None

    # Check tel: links
    tel_link = soup.find("a", href=re.compile(r"^tel:", re.IGNORECASE))
    if tel_link and tel_link.get("href"):
        phone = tel_link["href"].replace("tel:", "").strip()

    # Check mailto: links
    mailto_link = soup.find("a", href=re.compile(r"^mailto:", re.IGNORECASE))
    if mailto_link and mailto_link.get("href"):
        email = mailto_link["href"].replace("mailto:", "").split("?")[0].strip()

    # Fallback regex search for business email
    if not email:
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", soup.get_text())
        if email_match:
            candidate = email_match.group(0)
            if not candidate.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
                email = candidate

    return {"phone": phone, "email": email}


async def perform_seo_audit(target_url: str) -> Dict[str, Any]:
    """
    Executes a comprehensive SEO and digital marketing opportunity audit on a target website.
    """
    findings: List[SEOFinding] = []
    opportunities: List[str] = []
    recommended_services: List[str] = []

    success, html, status_code, err_msg, final_url = await safe_fetch_page(target_url)

    if not success or not html:
        findings.append(SEOFinding(
            category="Accessibility & Uptime",
            finding="Website Unreachable or Inaccessible",
            evidence=f"Failed to establish connection: {err_msg}",
            impact="Critical",
            recommended_improvement="Restore website hosting, verify DNS records, and ensure firewall permits standard web traffic.",
            suggested_service="Website Hosting & Infrastructure Recovery",
            passed=False
        ))
        return {
            "audited_url": target_url,
            "final_url": final_url,
            "http_status": status_code,
            "is_https": target_url.startswith("https://"),
            "page_title": None,
            "meta_description": None,
            "h1_heading": None,
            "images_missing_alt_count": 0,
            "total_images_count": 0,
            "has_viewport": False,
            "has_robots_txt": False,
            "has_sitemap_xml": False,
            "has_contact_page": False,
            "internal_links_count": 0,
            "local_seo_indicators": "None",
            "findings": findings,
            "opportunities": ["Website Inaccessible"],
            "primary_recommended_service": "Website Hosting & Infrastructure Recovery",
            "extracted_contacts": {"phone": None, "email": None, "socials": {}},
            "overall_assessment": "Critical: The website cannot be reached by potential customers or search engines."
        }

    soup = BeautifulSoup(html, "lxml" if "lxml" in BeautifulSoup.__dict__ else "html.parser")

    # 1. SSL / HTTPS
    is_https = final_url.startswith("https://")
    if is_https:
        findings.append(SEOFinding(
            category="Security & Protocol",
            finding="SSL / HTTPS Secure Connection Active",
            evidence=f"Final URL uses secure HTTPS protocol ({final_url})",
            impact="Low",
            recommended_improvement="Maintain SSL certificate auto-renewals.",
            suggested_service="Security & SSL Monitoring",
            passed=True
        ))
    else:
        findings.append(SEOFinding(
            category="Security & Protocol",
            finding="Website Lacks SSL Encryption (Insecure HTTP)",
            evidence=f"Website loaded over insecure HTTP ({final_url})",
            impact="High",
            recommended_improvement="Install an SSL certificate and redirect all HTTP traffic to HTTPS.",
            suggested_service="SSL Installation & HTTPS Security Migration",
            passed=False
        ))
        opportunities.append("Insecure HTTP")
        recommended_services.append("SSL Installation & HTTPS Security Migration")

    # 2. Page Title
    title_tag = soup.find("title")
    title_text = title_tag.get_text().strip() if title_tag else None
    if not title_text:
        findings.append(SEOFinding(
            category="Search Engine Optimization",
            finding="Missing Page Title Tag",
            evidence="No <title> tag found on the homepage.",
            impact="High",
            recommended_improvement="Add a descriptive title tag (50–60 characters) incorporating primary service and city.",
            suggested_service="On-Page SEO Optimization",
            passed=False
        ))
        opportunities.append("Missing Page Title")
        recommended_services.append("On-Page SEO Optimization")
    elif len(title_text) < 25 or len(title_text) > 70:
        findings.append(SEOFinding(
            category="Search Engine Optimization",
            finding="Suboptimal Title Tag Length",
            evidence=f"Title length is {len(title_text)} characters ('{title_text[:40]}...')",
            impact="Medium",
            recommended_improvement="Optimize title tag length to between 30 and 65 characters to prevent truncation in search results.",
            suggested_service="On-Page SEO Optimization",
            passed=False
        ))
        opportunities.append("Suboptimal Title Tag")
    else:
        findings.append(SEOFinding(
            category="Search Engine Optimization",
            finding="Optimal Page Title Configured",
            evidence=f"Title '{title_text}' is {len(title_text)} characters long.",
            impact="Low",
            recommended_improvement="Keep page title aligned with targeting keywords.",
            suggested_service="SEO Keyword Targeting",
            passed=True
        ))

    # 3. Meta Description
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    meta_desc_text = meta_desc_tag.get("content", "").strip() if meta_desc_tag else None
    if not meta_desc_text:
        findings.append(SEOFinding(
            category="Search Engine Optimization",
            finding="Missing Meta Description",
            evidence="No <meta name='description'> tag found.",
            impact="High",
            recommended_improvement="Add an engaging meta description (120–160 characters) featuring a call-to-action to boost click-through rate.",
            suggested_service="On-Page SEO & Snippet Optimization",
            passed=False
        ))
        opportunities.append("Missing Meta Description")
        recommended_services.append("On-Page SEO & Snippet Optimization")
    else:
        findings.append(SEOFinding(
            category="Search Engine Optimization",
            finding="Meta Description Present",
            evidence=f"Meta description found ({len(meta_desc_text)} chars): '{meta_desc_text[:60]}...'",
            impact="Low",
            recommended_improvement="Regularly refresh meta descriptions to match promotional offers.",
            suggested_service="Snippet Optimization",
            passed=True
        ))

    # 4. H1 Heading
    h1_tags = soup.find_all("h1")
    h1_text = h1_tags[0].get_text().strip() if h1_tags else None
    if not h1_tags:
        findings.append(SEOFinding(
            category="On-Page Structure",
            finding="Missing H1 Main Heading",
            evidence="No <h1> heading found on the page.",
            impact="Medium",
            recommended_improvement="Add a single <h1> heading defining the company's core value proposition.",
            suggested_service="Content & On-Page Structure Optimization",
            passed=False
        ))
        opportunities.append("Missing H1 Heading")
        recommended_services.append("Content & On-Page Structure Optimization")
    elif len(h1_tags) > 1:
        findings.append(SEOFinding(
            category="On-Page Structure",
            finding="Multiple H1 Headings Detected",
            evidence=f"Found {len(h1_tags)} separate <h1> tags on the homepage.",
            impact="Low",
            recommended_improvement="Use exactly one primary <h1> heading for the main topic and structure sub-sections using <h2> and <h3> tags.",
            suggested_service="Semantic HTML & Heading Structure Clean-up",
            passed=False
        ))
    else:
        findings.append(SEOFinding(
            category="On-Page Structure",
            finding="Single Primary H1 Heading Configured",
            evidence=f"H1: '{h1_text[:60]}'",
            impact="Low",
            recommended_improvement="Ensure H1 includes the primary service benefit.",
            suggested_service="Content Strategy",
            passed=True
        ))

    # 5. Mobile Viewport
    viewport_tag = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
    has_viewport = bool(viewport_tag and "width=" in viewport_tag.get("content", ""))
    if not has_viewport:
        findings.append(SEOFinding(
            category="Mobile & Responsiveness",
            finding="Missing Mobile Viewport Meta Tag",
            evidence="No `<meta name='viewport'>` tag configured.",
            impact="High",
            recommended_improvement="Add mobile viewport tag and ensure responsive design across smartphone screens.",
            suggested_service="Mobile Optimization & Responsive Web Redesign",
            passed=False
        ))
        opportunities.append("Missing Mobile Viewport")
        recommended_services.append("Mobile Optimization & Responsive Web Redesign")
    else:
        findings.append(SEOFinding(
            category="Mobile & Responsiveness",
            finding="Mobile Viewport Meta Tag Present",
            evidence=f"Viewport tag content: '{viewport_tag.get('content')}'",
            impact="Low",
            recommended_improvement="Audit site speed on mobile networks.",
            suggested_service="Mobile UX Testing",
            passed=True
        ))

    # 6. Image Alt Attributes
    images = soup.find_all("img")
    total_images = len(images)
    missing_alt = sum(1 for img in images if not img.get("alt") or not img.get("alt").strip())
    if total_images > 0 and missing_alt > 0:
        findings.append(SEOFinding(
            category="Accessibility & Image SEO",
            finding="Images Missing Descriptive Alt Text",
            evidence=f"{missing_alt} out of {total_images} images lack descriptive alt attributes.",
            impact="Medium",
            recommended_improvement="Add descriptive, keyword-relevant alt text to all informative images.",
            suggested_service="Image SEO & Web Accessibility (ADA) Enhancement",
            passed=False
        ))
        opportunities.append("Missing Image Alt Tags")
        recommended_services.append("Image SEO & Web Accessibility (ADA) Enhancement")
    elif total_images > 0:
        findings.append(SEOFinding(
            category="Accessibility & Image SEO",
            finding="All Images Have Alt Attributes",
            evidence=f"All {total_images} images include alt text.",
            impact="Low",
            recommended_improvement="Periodically audit new image uploads.",
            suggested_service="Content Maintenance",
            passed=True
        ))

    # 7. Contact Page & Conversion Indicators
    contact_links = [
        a["href"] for a in soup.find_all("a", href=True)
        if any(w in a["href"].lower() for w in ["contact", "contact-us", "reach-us", "get-in-touch", "appointment", "book"])
    ]
    has_contact_page = len(contact_links) > 0
    if not has_contact_page:
        findings.append(SEOFinding(
            category="Conversion & Lead Capture",
            finding="No Dedicated Contact Page Link Detected",
            evidence="Homepage navigation does not feature an explicit link to a contact page.",
            impact="Medium",
            recommended_improvement="Add a clear 'Contact Us' or 'Book Consultation' button in the main header navigation.",
            suggested_service="Conversion Rate Optimization (CRO)",
            passed=False
        ))
        opportunities.append("No Clear Contact Page")
        recommended_services.append("Conversion Rate Optimization (CRO)")
    else:
        findings.append(SEOFinding(
            category="Conversion & Lead Capture",
            finding="Dedicated Contact Link Present",
            evidence=f"Found contact link: '{contact_links[0]}'",
            impact="Low",
            recommended_improvement="Optimize contact form fields to reduce friction.",
            suggested_service="Lead Capture Optimization",
            passed=True
        ))

    # 8. Local SEO & Schema Indicators
    schemas = soup.find_all("script", attrs={"type": "application/ld+json"})
    has_local_schema = False
    for sc in schemas:
        try:
            sc_data = json.loads(sc.get_text())
            if isinstance(sc_data, dict):
                sc_type = str(sc_data.get("@type", "")).lower()
                if any(x in sc_type for x in ["localbusiness", "organization", "store", "restaurant", "clinic", "dentist", "attorney", "contractor"]):
                    has_local_schema = True
                    break
        except Exception:
            pass

    tel_links = soup.find_all("a", href=re.compile(r"^tel:", re.I))
    has_click_to_call = len(tel_links) > 0

    local_signals = []
    if has_local_schema:
        local_signals.append("LocalBusiness Schema JSON-LD")
    if has_click_to_call:
        local_signals.append(f"Click-to-call link ({tel_links[0]['href']})")

    if not local_signals:
        findings.append(SEOFinding(
            category="Local SEO",
            finding="Missing Local SEO Schema & Click-to-Call Buttons",
            evidence="No Schema.org LocalBusiness structured data or click-to-call links found.",
            impact="High",
            recommended_improvement="Embed JSON-LD LocalBusiness markup and add tap-to-call phone buttons for mobile visitors.",
            suggested_service="Local SEO & Google Business Profile Optimization",
            passed=False
        ))
        opportunities.append("Missing Local Schema & Call CTAs")
        recommended_services.append("Local SEO & Google Business Profile Optimization")
    else:
        findings.append(SEOFinding(
            category="Local SEO",
            finding="Local SEO Signals Present",
            evidence=f"Found: {', '.join(local_signals)}",
            impact="Low",
            recommended_improvement="Keep NAP (Name, Address, Phone) consistent with Google Maps listing.",
            suggested_service="Local Citation Management",
            passed=True
        ))

    # 9. Robots.txt and Sitemap.xml
    has_robots = await check_url_exists(final_url, "/robots.txt")
    has_sitemap = await check_url_exists(final_url, "/sitemap.xml")

    if not has_sitemap:
        findings.append(SEOFinding(
            category="Crawlability & Indexing",
            finding="XML Sitemap Not Detected at /sitemap.xml",
            evidence="Request to /sitemap.xml did not return HTTP 200.",
            impact="Medium",
            recommended_improvement="Generate an automated XML sitemap and submit to Google Search Console.",
            suggested_service="Technical SEO & Indexing Setup",
            passed=False
        ))
        opportunities.append("Missing XML Sitemap")
        recommended_services.append("Technical SEO & Indexing Setup")
    else:
        findings.append(SEOFinding(
            category="Crawlability & Indexing",
            finding="XML Sitemap Detected",
            evidence="/sitemap.xml responded successfully.",
            impact="Low",
            recommended_improvement="Ensure sitemap updates dynamically when new pages publish.",
            suggested_service="Technical Maintenance",
            passed=True
        ))

    # 10. Social Media Links
    social_links = extract_social_links(soup)
    missing_socials = [k for k, v in {"LinkedIn": social_links.get("linkedin"), "Facebook": social_links.get("facebook"), "Instagram": social_links.get("instagram")}.items() if not v]
    if len(missing_socials) >= 2:
        findings.append(SEOFinding(
            category="Social Media & Branding",
            finding="Limited Social Media Presence Linked",
            evidence=f"Homepage does not link to {', '.join(missing_socials)}.",
            impact="Low",
            recommended_improvement="Set up official brand social profiles and link them in the website footer.",
            suggested_service="Social Media Management & Branding",
            passed=False
        ))
        opportunities.append("Limited Social Links")
        recommended_services.append("Social Media Management & Branding")

    # Count internal links
    internal_links_count = 0
    parsed_base = urlparse(final_url)
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        parsed_href = urlparse(href)
        if not parsed_href.netloc or parsed_href.netloc.lower() == parsed_base.netloc.lower():
            internal_links_count += 1

    # Extract public contact info for enrichment
    extracted_contacts = extract_contact_info_from_html(soup)
    extracted_contacts["socials"] = social_links

    # Primary recommended service
    primary_service = recommended_services[0] if recommended_services else "Digital Marketing Growth & Retainer"

    # Overall assessment
    failed_count = sum(1 for f in findings if not f.passed)
    if failed_count >= 5:
        assessment = f"Significant digital marketing and technical SEO opportunities identified ({failed_count} optimization areas found)."
    elif failed_count >= 2:
        assessment = f"Moderate digital marketing opportunities identified ({failed_count} optimization areas found)."
    else:
        assessment = "Website technical fundamentals are strong; recommend growth marketing and targeted traffic generation."

    return {
        "audited_url": target_url,
        "final_url": final_url,
        "http_status": status_code,
        "is_https": is_https,
        "page_title": title_text,
        "meta_description": meta_desc_text,
        "h1_heading": h1_text,
        "images_missing_alt_count": missing_alt,
        "total_images_count": total_images,
        "has_viewport": has_viewport,
        "has_robots_txt": has_robots,
        "has_sitemap_xml": has_sitemap,
        "has_contact_page": has_contact_page,
        "internal_links_count": internal_links_count,
        "local_seo_indicators": ", ".join(local_signals) if local_signals else "None detected",
        "findings": findings,
        "opportunities": opportunities,
        "primary_recommended_service": primary_service,
        "extracted_contacts": extracted_contacts,
        "overall_assessment": assessment
    }

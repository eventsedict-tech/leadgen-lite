import pytest
from bs4 import BeautifulSoup
from app.core.ssrf import validate_url_for_ssrf
from app.services.seo_auditor import extract_contact_info_from_html, extract_social_links


def test_ssrf_protection_filters():
    safe, err, _ = validate_url_for_ssrf("http://127.0.0.1:8080/admin")
    assert not safe
    assert "loopback" in err.lower() or "blocked" in err.lower()

    safe, err, _ = validate_url_for_ssrf("http://localhost:5000/api")
    assert not safe

    safe, err, _ = validate_url_for_ssrf("http://169.254.169.254/latest/meta-data/")
    assert not safe

    safe, err, _ = validate_url_for_ssrf("http://192.168.1.1/router")
    assert not safe

    safe, err, _ = validate_url_for_ssrf("http://10.0.0.5:3000/db")
    assert not safe

    safe, err, _ = validate_url_for_ssrf("ftp://files.example.com")
    assert not safe

    safe, err, _ = validate_url_for_ssrf("file:///etc/passwd")
    assert not safe


def test_html_parsing_and_contact_extraction():
    html_sample = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Austin Prime Roofing - Roof Repair & Installation</title>
        <meta name="description" content="Award-winning residential roofing contractors serving the Austin metro. Get a free estimate today.">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <h1>Austin's Premier Roofing Specialists</h1>
        <p>Call us today at <a href="tel:+15125559988">+1 512-555-9988</a> or email <a href="mailto:contact@austinprimeroofing.com">contact@austinprimeroofing.com</a></p>
        <img src="/logo.png" alt="Austin Prime Roofing Logo">
        <img src="/banner.jpg">
        <a href="/contact-us">Contact Our Team</a>
        <a href="https://linkedin.com/company/austinprimeroofing">LinkedIn</a>
    </body>
    </html>
    """
    soup = BeautifulSoup(html_sample, "html.parser")
    contacts = extract_contact_info_from_html(soup)
    assert contacts["phone"] == "+15125559988"
    assert contacts["email"] == "contact@austinprimeroofing.com"

    socials = extract_social_links(soup)
    assert "linkedin" in socials
    assert "austinprimeroofing" in socials["linkedin"]


def test_enrichment_and_audit_api(client):
    reg = client.post("/api/auth/register", json={
        "email": "auditor_suite@test.com",
        "password": "Password123!",
        "full_name": "Audit Specialist",
        "organization_name": "Growth Lab Suite"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    no_web_lead = client.post("/api/leads", json={
        "company_name": "Lone Star Plumbing LLC",
        "official_website": None,
        "city": "Dallas"
    }, headers=headers).json()

    enrich_res = client.post(f"/api/enrichment/queue/{no_web_lead['id']}", headers=headers)
    assert enrich_res.status_code == 200
    assert enrich_res.json()["status"] == "completed"

    lead_check = client.get(f"/api/leads/{no_web_lead['id']}", headers=headers).json()
    assert "website" in lead_check["marketing_opportunity"].lower()
    assert "Web Design" in lead_check["recommended_service"]

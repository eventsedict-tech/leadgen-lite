import pytest


def test_scoring_and_manual_override(client):
    reg = client.post("/api/auth/register", json={
        "email": "scorer_suite@test.com",
        "password": "Password123!",
        "full_name": "Scoring Lead",
        "organization_name": "Precision SEO Suite"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    lead_res = client.post("/api/leads", json={
        "company_name": "Austin Spine & Orthopedics Center",
        "official_website": None,
        "industry": "Healthcare",
        "city": "Austin",
        "country": "USA",
        "public_business_phone": "+1-512-555-8899",
        "general_business_email": "info@austinspine.com",
        "publicly_listed_contact_name": "Dr. Marcus Vance"
    }, headers=headers)
    assert lead_res.status_code == 201
    lead_id = lead_res.json()["id"]

    score_res = client.post(f"/api/scoring/calculate/{lead_id}", headers=headers)
    assert score_res.status_code == 200
    score_data = score_res.json()
    assert score_data["total_score"] >= 70
    assert score_data["priority_tier"] in ("High Priority", "Medium Priority")
    assert len(score_data["breakdown"]) == 5

    override_res = client.post(f"/api/scoring/override/{lead_id}", json={
        "new_score": 95,
        "override_reason": "Direct VIP referral with budget ready"
    }, headers=headers)
    assert override_res.status_code == 200
    override_data = override_res.json()
    assert override_data["total_score"] == 95
    assert override_data["priority_tier"] == "High Priority"
    assert override_data["manual_override"] is True

    history_res = client.get(f"/api/scoring/history/{lead_id}", headers=headers)
    assert history_res.status_code == 200
    assert len(history_res.json()) >= 2


def test_outreach_generation_english_and_hindi(client):
    reg = client.post("/api/auth/register", json={
        "email": "outreach_suite@test.com",
        "password": "Password123!",
        "full_name": "Outreach Specialist",
        "organization_name": "Global Outreach Suite"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    lead_res = client.post("/api/leads", json={
        "company_name": "Apex Solar Solutions",
        "official_website": "https://apexsolarsolutions.com",
        "industry": "Clean Energy",
        "city": "Jaipur",
        "public_business_phone": "+91-98765-43210",
        "general_business_email": "contact@apexsolar.com",
        "publicly_listed_contact_name": "Rajesh Sharma"
    }, headers=headers)
    lead_id = lead_res.json()["id"]

    email_en = client.post("/api/outreach/generate", json={
        "lead_id": lead_id,
        "channel": "cold_email",
        "language": "en"
    }, headers=headers)
    assert email_en.status_code == 200
    data_en = email_en.json()
    assert "Apex Solar Solutions" in data_en["message_body"]
    assert "Rajesh Sharma" in data_en["message_body"]
    assert data_en["subject_line"] is not None

    email_hi = client.post("/api/outreach/generate", json={
        "lead_id": lead_id,
        "channel": "cold_email",
        "language": "hi"
    }, headers=headers)
    assert email_hi.status_code == 200
    data_hi = email_hi.json()
    assert "नमस्ते Rajesh Sharma" in data_hi["message_body"] or "नमस्ते" in data_hi["message_body"]
    assert "Apex Solar Solutions" in data_hi["message_body"]

    li_note = client.post("/api/outreach/generate", json={
        "lead_id": lead_id,
        "channel": "linkedin_note",
        "language": "en"
    }, headers=headers)
    assert li_note.status_code == 200
    note_body = li_note.json()["message_body"]
    assert len(note_body) <= 300

    wa_draft = client.post("/api/outreach/generate", json={
        "lead_id": lead_id,
        "channel": "whatsapp_draft",
        "language": "hi"
    }, headers=headers)
    assert wa_draft.status_code == 200
    assert "व्हाट्सएप" in wa_draft.json()["suggested_next_action"] or "नमस्ते" in wa_draft.json()["message_body"]

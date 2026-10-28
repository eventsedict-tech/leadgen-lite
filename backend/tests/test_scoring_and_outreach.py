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


def test_outreach_dispatch_integrations(client):
    reg = client.post("/api/auth/register", json={
        "email": "dispatch_tester@test.com",
        "password": "Password123!",
        "full_name": "Dispatch Agent",
        "organization_name": "Multi Channel Outreach Org"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    lead_res = client.post("/api/leads", json={
        "company_name": "Zenith Marketing Tech",
        "official_website": "https://zenithmarketing.tech",
        "industry": "Marketing",
        "city": "Bengaluru",
        "public_business_phone": "+91-91234-56789",
        "general_business_email": "hello@zenithmarketing.tech",
        "publicly_listed_contact_name": "Priya Nair"
    }, headers=headers)
    lead_id = lead_res.json()["id"]

    # 1. Channels status
    status_res = client.get("/api/outreach/channels/status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "email_smtp_ready" in status_data
    assert status_data["whatsapp_web_ready"] is True
    assert status_data["linkedin_ready"] is True

    # 2. Email Outreach Dispatch
    email_res = client.post("/api/outreach/send/email", json={
        "lead_id": lead_id,
        "subject": "Quick intro for Zenith Marketing",
        "message_body": "Hi Priya, hope all is well."
    }, headers=headers)
    assert email_res.status_code == 200, f"Error: {email_res.status_code} - {email_res.text}"
    assert email_res.json()["success"] is True
    assert "mailto:" in email_res.json()["link"]

    # Check lead updated to Contacted
    updated_lead = client.get(f"/api/leads/{lead_id}", headers=headers).json()
    assert updated_lead["crm_status"] == "Contacted"

    # 3. WhatsApp Outreach Dispatch
    wa_res = client.post("/api/outreach/send/whatsapp", json={
        "lead_id": lead_id,
        "message_body": "Hello Priya, greetings from our team."
    }, headers=headers)
    assert wa_res.status_code == 200
    assert wa_res.json()["success"] is True
    assert "wa.me" in wa_res.json()["link"]
    assert "919123456789" in wa_res.json()["link"]

    # 4. LinkedIn Outreach Dispatch
    li_res = client.post("/api/outreach/send/linkedin", json={
        "lead_id": lead_id,
        "action_type": "connection_note",
        "message_body": "Hi Priya, loved your work at Zenith Marketing!"
    }, headers=headers)
    assert li_res.status_code == 200, f"Error: {li_res.status_code} - {li_res.text}"
    assert li_res.json()["success"] is True
    assert "linkedin.com" in li_res.json()["link"]

    # Check that a follow-up task was scheduled
    tasks_res = client.get(f"/api/tasks?lead_id={lead_id}", headers=headers)
    assert tasks_res.status_code == 200
    assert len(tasks_res.json()) >= 1
    assert "LinkedIn" in tasks_res.json()[0]["title"]


def test_bulk_outreach_and_campaigns(client):
    reg = client.post("/api/auth/register", json={
        "email": "bulk_tester@test.com",
        "password": "Password123!",
        "full_name": "Bulk Outreach Lead",
        "organization_name": "Growth Agency Ltd"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create 2 leads
    res1 = client.post("/api/leads", json={
        "company_name": "Alpha Corp",
        "industry": "Consulting",
        "city": "Mumbai",
        "public_business_phone": "+91-99887-11223",
        "general_business_email": "contact@alphacorp.test",
        "publicly_listed_contact_name": "Aakash Mehta"
    }, headers=headers)
    assert res1.status_code == 201
    l1 = res1.json()

    res2 = client.post("/api/leads", json={
        "company_name": "Beta Digital",
        "industry": "Marketing",
        "city": "Pune",
        "public_business_phone": "+91-99887-44556",
        "general_business_email": "contact@betadigital.test",
        "publicly_listed_contact_name": "Bhavna Patel"
    }, headers=headers)
    assert res2.status_code == 201
    l2 = res2.json()

    lead_ids = [l1["id"], l2["id"]]

    # 1. Bulk generate drafts
    gen_res = client.post("/api/outreach/bulk/generate", json={
        "lead_ids": lead_ids,
        "channel": "cold_email",
        "language": "en"
    }, headers=headers)
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert len(gen_data) == 2
    assert gen_data[0]["channel"] == "cold_email"

    # 2. Bulk send email
    send_res = client.post("/api/outreach/bulk/send/email", json={
        "lead_ids": lead_ids,
        "channel": "cold_email",
        "language": "en"
    }, headers=headers)
    assert send_res.status_code == 200
    send_data = send_res.json()
    assert send_data["total_requested"] == 2
    assert send_data["processed_count"] == 2
    assert send_data["success_count"] == 2

    # Check that leads are now Contacted
    check_l1 = client.get(f"/api/leads/{l1['id']}", headers=headers).json()
    assert check_l1["crm_status"] == "Contacted"

    # 3. Create Campaign
    camp_res = client.post("/api/outreach/campaigns", json={
        "name": "Q4 High Priority Outreach",
        "channel": "cold_email",
        "lead_ids": lead_ids,
        "sending_limit_per_day": 50,
        "language": "en"
    }, headers=headers)
    assert camp_res.status_code == 200
    camp_data = camp_res.json()
    assert camp_data["name"] == "Q4 High Priority Outreach"
    assert camp_data["recipient_count"] == 2
    camp_id = camp_data["id"]

    # 4. List Campaigns
    list_res = client.get("/api/outreach/campaigns", headers=headers)
    assert list_res.status_code == 200
    camps = list_res.json()
    assert len(camps) >= 1
    target = next((c for c in camps if c["id"] == camp_id), None)
    assert target is not None
    assert target["recipient_count"] == 2

    # 5. Get Campaign Detail
    detail_res = client.get(f"/api/outreach/campaigns/{camp_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["name"] == "Q4 High Priority Outreach"
    assert len(detail["recipients"]) == 2


import pytest


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_user_registration_and_login(client):
    reg_data = {
        "email": "test_auth_user@leadgenlite.com",
        "password": "SecurePassword123!",
        "full_name": "Test Marketer",
        "organization_name": "Growth Agency"
    }
    res = client.post("/api/auth/register", json=reg_data)
    assert res.status_code == 201
    token_data = res.json()
    assert "access_token" in token_data
    assert token_data["user"]["email"] == "test_auth_user@leadgenlite.com"
    token = token_data["access_token"]

    login_res = client.post("/api/auth/login", json={
        "email": "test_auth_user@leadgenlite.com",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["full_name"] == "Test Marketer"


def test_lead_lifecycle_and_deduplication(client):
    reg_data = {
        "email": "agency_dedupe@test.com",
        "password": "Password123!",
        "full_name": "Agency User",
        "organization_name": "Digital Boost"
    }
    res = client.post("/api/auth/register", json=reg_data)
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    lead_data = {
        "company_name": "Apex Dental Clinic LLC",
        "official_website": "https://www.apexdental.com/contact",
        "industry": "Healthcare",
        "city": "Austin",
        "public_business_phone": "+1-512-555-0199",
        "general_business_email": "contact@apexdental.com"
    }
    create_res = client.post("/api/leads", json=lead_data, headers=headers)
    assert create_res.status_code == 201
    lead = create_res.json()
    lead_id = lead["id"]
    assert lead["normalized_domain"] == "apexdental.com"
    assert lead["crm_status"] == "New"

    dup_data = {
        "company_name": "Apex Dental Clinic",
        "official_website": "http://apexdental.com",
        "industry": "Healthcare"
    }
    dup_res = client.post("/api/leads", json=dup_data, headers=headers)
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"]

    list_res = client.get("/api/leads?city=Austin", headers=headers)
    assert list_res.status_code == 200
    list_json = list_res.json()
    assert list_json["total"] >= 1

    update_res = client.put(f"/api/leads/{lead_id}", json={"crm_status": "Qualified"}, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["crm_status"] == "Qualified"

    del_res = client.delete(f"/api/leads/{lead_id}", headers=headers)
    assert del_res.status_code == 204

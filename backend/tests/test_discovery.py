import pytest


def test_discovery_pipeline_and_guards(client):
    reg = client.post("/api/auth/register", json={
        "email": "hunter_suite@test.com",
        "password": "Password123!",
        "full_name": "Lead Hunter",
        "organization_name": "Discovery Labs"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    prov_res = client.get("/api/discovery/providers", headers=headers)
    assert prov_res.status_code == 200
    providers = prov_res.json()
    provider_ids = [p["id"] for p in providers]
    assert "google_places" in provider_ids
    assert "search_api" in provider_ids
    assert "test_mock" in provider_ids

    places_prov = next(p for p in providers if p["id"] == "google_places")
    if not places_prov["is_configured"]:
        unconf_res = client.post("/api/discovery/search", json={
            "provider_id": "google_places",
            "query": {"city": "Austin", "industry": "Dentists"}
        }, headers=headers)
        assert unconf_res.status_code == 400
        assert "not configured" in unconf_res.json()["detail"].lower()

    search_res = client.post("/api/discovery/search", json={
        "provider_id": "test_mock",
        "query": {"city": "Austin", "industry": "Healthcare", "limit": 10}
    }, headers=headers)
    assert search_res.status_code == 200
    companies = search_res.json()
    assert len(companies) > 0
    assert any("Dental" in c["company_name"] for c in companies)

    import_res = client.post("/api/discovery/import-selected", json={
        "companies": companies
    }, headers=headers)
    assert import_res.status_code == 200
    import_data = import_res.json()
    assert import_data["imported"] > 0
    assert import_data["skipped_duplicates"] == 0

    reimport_res = client.post("/api/discovery/import-selected", json={
        "companies": companies
    }, headers=headers)
    assert reimport_res.status_code == 200
    reimport_data = reimport_res.json()
    assert reimport_data["imported"] == 0
    assert reimport_data["skipped_duplicates"] == len(companies)

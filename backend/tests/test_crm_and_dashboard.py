from datetime import datetime, timedelta, timezone
import pytest


def test_crm_tasks_suppression_and_dashboard(client):
    reg = client.post("/api/auth/register", json={
        "email": "manager_suite@test.com",
        "password": "Password123!",
        "full_name": "CRM Manager",
        "organization_name": "Apex Marketing Suite"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    lead1 = client.post("/api/leads", json={
        "company_name": "Blue Horizon Dental",
        "official_website": "https://bluehorizondental.com",
        "industry": "Healthcare",
        "city": "Austin",
        "general_business_email": "reception@bluehorizondental.com"
    }, headers=headers).json()

    lead2 = client.post("/api/leads", json={
        "company_name": "Austin Law Group",
        "industry": "Legal",
        "city": "Austin",
        "general_business_email": "optout@austinlaw.com"
    }, headers=headers).json()

    due = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    task_res = client.post("/api/tasks", json={
        "lead_id": lead1["id"],
        "title": "Call Dr. Horizon for SEO Discovery",
        "due_date": due,
        "notes": "Follow up on free audit proposal"
    }, headers=headers)
    assert task_res.status_code == 201
    task = task_res.json()
    assert task["company_name"] == "Blue Horizon Dental"
    assert task["status"] == "pending"

    tasks_res = client.get("/api/tasks?status_filter=pending", headers=headers)
    assert len(tasks_res.json()) >= 1

    comp_res = client.put(f"/api/tasks/{task['id']}", json={"status": "completed"}, headers=headers)
    assert comp_res.json()["status"] == "completed"

    supp_res = client.post("/api/suppression", json={
        "email": "optout@austinlaw.com",
        "reason": "Client requested unsubscribe"
    }, headers=headers)
    assert supp_res.status_code == 201

    updated_lead2 = client.get(f"/api/leads/{lead2['id']}", headers=headers).json()
    assert updated_lead2["crm_status"] == "Do Not Contact"

    dash_res = client.get("/api/dashboard/metrics", headers=headers)
    assert dash_res.status_code == 200
    metrics = dash_res.json()["metrics"]
    assert metrics["total_leads"] >= 2
    distributions = dash_res.json()["distributions"]
    assert len(distributions["by_city"]) >= 1

    int_res = client.get("/api/settings/integrations", headers=headers)
    assert int_res.status_code == 200
    providers = [p["provider_type"] for p in int_res.json()]
    assert "google_places" in providers
    assert "smtp" in providers

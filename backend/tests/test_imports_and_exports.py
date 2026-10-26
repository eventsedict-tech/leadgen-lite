import io
import pytest
from app.services.export_service import sanitize_formula_injection


def test_formula_injection_defense():
    assert sanitize_formula_injection("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert sanitize_formula_injection("+123456") == "'+123456"
    assert sanitize_formula_injection("-SUM(A1:B10)") == "'-SUM(A1:B10)"
    assert sanitize_formula_injection("@SUM(A1)") == "'@SUM(A1)"
    assert sanitize_formula_injection("Acme Marketing Inc.") == "Acme Marketing Inc."
    assert sanitize_formula_injection(123) == 123


def test_csv_upload_mapping_and_import(client):
    reg = client.post("/api/auth/register", json={
        "email": "importer_suite@test.com",
        "password": "Password123!",
        "full_name": "Data Analyst",
        "organization_name": "Acme Importers"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    csv_content = """Company,Website,Email,Phone,City,Industry
Nova Solar LLC,https://novasolar.com,info@novasolar.com,+1-512-555-1100,Austin,Clean Energy
Blue Wave Dental,https://bluewavedental.com,contact@bluewavedental.com,+1-512-555-2200,Austin,Healthcare
,https://invalid.com,no-name@invalid.com,,Austin,Unknown
"""
    files = {"file": ("test_leads.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}

    preview_res = client.post("/api/imports/preview", files=files, headers=headers)
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["total_detected_rows"] == 3
    assert "Company" in preview_data["suggested_mappings"]
    assert preview_data["suggested_mappings"]["Company"] == "company_name"
    assert preview_data["suggested_mappings"]["Website"] == "official_website"
    temp_file_id = preview_data["temp_file_id"]

    val_res = client.post("/api/imports/validate", json={
        "temp_file_id": temp_file_id,
        "column_mapping": preview_data["suggested_mappings"],
        "skip_duplicates": True,
        "merge_existing": False
    }, headers=headers)
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["valid_new_records"] == 2
    assert val_data["invalid_records"] == 1

    commit_res = client.post("/api/imports/commit", json={
        "temp_file_id": temp_file_id,
        "column_mapping": preview_data["suggested_mappings"],
        "skip_duplicates": True,
        "merge_existing": False
    }, headers=headers)
    assert commit_res.status_code == 200
    commit_data = commit_res.json()
    assert commit_data["imported_records"] == 2
    assert commit_data["skipped_records"] == 1

    leads_res = client.get("/api/leads", headers=headers)
    assert leads_res.status_code == 200
    assert leads_res.json()["total"] == 2

    export_xlsx_res = client.get("/api/exports/leads?format=xlsx", headers=headers)
    assert export_xlsx_res.status_code == 200
    assert len(export_xlsx_res.content) > 0

    export_csv_res = client.get("/api/exports/leads?format=csv", headers=headers)
    assert export_csv_res.status_code == 200
    assert b"Nova Solar LLC" in export_csv_res.content
    assert b"novasolar.com" in export_csv_res.content

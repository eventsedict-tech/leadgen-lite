import os
import uuid
import json
import re
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Lead, ImportJob, AuditLog
from app.models.enums import CRMStage, VerificationStatus, LeadPriority
from app.services.deduplication import (
    normalize_company_name, extract_domain, find_existing_lead, check_is_suppressed
)

# Column mapping heuristics: Target Field -> list of lowercased header synonyms
MAPPING_SYNONYMS: Dict[str, List[str]] = {
    "company_name": ["company", "company name", "business name", "organization", "account name", "name", "firm", "business", "company_name"],
    "official_website": ["website", "site", "web", "url", "domain", "homepage", "web address", "official website", "official_website"],
    "general_business_email": ["email", "mail", "contact email", "business email", "e-mail", "email address", "general_business_email"],
    "public_business_phone": ["phone", "telephone", "mobile", "contact number", "phone number", "tel", "cell", "public_business_phone"],
    "industry": ["industry", "sector", "vertical", "business category", "category", "niche"],
    "city": ["city", "town", "metro", "municipality", "location city"],
    "state": ["state", "province", "region"],
    "country": ["country", "nation"],
    "public_business_address": ["address", "street", "street address", "location", "full address", "business address"],
    "publicly_listed_contact_name": ["contact person", "contact name", "full name", "first name", "decision maker", "owner", "ceo", "director", "contact"],
    "publicly_listed_designation": ["title", "designation", "job title", "role", "position"],
    "company_linkedin_url": ["linkedin", "linkedin url", "company linkedin", "linkedin profile"],
    "source_url": ["source", "source url", "lead source", "source link"]
}


def clean_cell_value(val: Any) -> Optional[str]:
    """Clean and standardize a cell value, returning None if empty or invalid."""
    if val is None:
        return None
    s = str(val).strip()
    if s.lower() in ("", "none", "nan", "null", "undefined"):
        return None
    return s


def guess_column_mappings(headers: List[str]) -> Dict[str, str]:
    """Suggests mappings from file headers to Lead model fields."""
    suggested: Dict[str, str] = {}
    assigned_targets = set()

    for header in headers:
        clean_header = re.sub(r"[^\w\s]", "", str(header).lower()).strip()
        matched_target = None

        for target_field, synonyms in MAPPING_SYNONYMS.items():
            if target_field in assigned_targets:
                continue
            if clean_header in synonyms or any(syn in clean_header for syn in synonyms):
                matched_target = target_field
                break
        
        if matched_target:
            suggested[header] = matched_target
            assigned_targets.add(matched_target)
        else:
            suggested[header] = "ignore"

    return suggested


def read_file_dataframe(file_path: str) -> pd.DataFrame:
    """Reads a CSV or Excel file safely into a pandas DataFrame."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path)
    elif ext == ".csv":
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding="latin-1")
    else:
        raise ValueError(f"Unsupported file format: {ext}. Only CSV and XLSX are supported.")
    
    # Replace NaN with None
    return df.where(pd.notnull(df), None)


def parse_and_preview_file(file_path: str, filename: str) -> Dict[str, Any]:
    """Loads file, extracts headers, first 5 sample rows, and generates suggested mappings."""
    df = read_file_dataframe(file_path)
    headers = [str(c) for c in df.columns.tolist()]
    total_rows = len(df)
    
    sample_df = df.head(5)
    sample_rows = sample_df.to_dict(orient="records")
    
    suggested_mappings = guess_column_mappings(headers)

    return {
        "filename": filename,
        "total_detected_rows": total_rows,
        "headers": headers,
        "sample_rows": sample_rows,
        "suggested_mappings": suggested_mappings
    }


def validate_import_preview(
    db: Session,
    org_id: int,
    file_path: str,
    column_mapping: Dict[str, str]
) -> Dict[str, Any]:
    """
    Simulates import with column mapping, detects duplicates, counts valid/invalid records,
    and returns a preview of how rows will be handled.
    """
    df = read_file_dataframe(file_path)
    total_rows = len(df)
    
    valid_new = 0
    duplicates = 0
    invalid = 0
    preview_items = []

    target_to_header = {v: k for k, v in column_mapping.items() if v != "ignore"}

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        comp_name = clean_cell_value(row_dict.get(target_to_header.get("company_name", "")))
        website = clean_cell_value(row_dict.get(target_to_header.get("official_website", "")))
        email = clean_cell_value(row_dict.get(target_to_header.get("general_business_email", "")))
        phone = clean_cell_value(row_dict.get(target_to_header.get("public_business_phone", "")))

        if not comp_name:
            invalid += 1
            action = "INVALID: Missing Company Name"
        else:
            domain = extract_domain(website or email)
            existing = find_existing_lead(db, org_id, comp_name, domain)
            if existing:
                duplicates += 1
                action = f"DUPLICATE (Matches ID: {existing.id} '{existing.company_name}')"
            else:
                valid_new += 1
                action = "NEW_RECORD"

        if idx < 10:
            preview_items.append({
                "row_index": int(idx + 1),
                "company_name": comp_name or "(Missing)",
                "website": website or None,
                "email": email or None,
                "phone": phone or None,
                "action": action
            })

    return {
        "total_rows": total_rows,
        "valid_new_records": valid_new,
        "duplicate_records": duplicates,
        "invalid_records": invalid,
        "preview_items": preview_items
    }


def execute_import(
    db: Session,
    org_id: int,
    user_id: int,
    file_path: str,
    filename: str,
    column_mapping: Dict[str, str],
    skip_duplicates: bool = True,
    merge_existing: bool = False
) -> Dict[str, Any]:
    """
    Executes the validated import into the database.
    Does not overwrite verified/existing non-empty fields with empty values.
    Logs errors and generates an ImportJob record.
    """
    df = read_file_dataframe(file_path)
    target_to_header = {v: k for k, v in column_mapping.items() if v != "ignore"}

    total_records = len(df)
    imported = 0
    skipped = 0
    merged = 0
    errors = []

    for idx, row in df.iterrows():
        row_num = int(idx + 1)
        row_dict = row.to_dict()

        def get_val(target_key: str) -> Optional[str]:
            col = target_to_header.get(target_key)
            if col and col in row_dict:
                return clean_cell_value(row_dict[col])
            return None

        comp_name = get_val("company_name")
        if not comp_name:
            skipped += 1
            errors.append({"row": row_num, "error": "Missing required company name", "data": row_dict})
            continue

        website = get_val("official_website")
        email = get_val("general_business_email")
        phone = get_val("public_business_phone")
        domain = extract_domain(website or email)
        norm_name = normalize_company_name(comp_name)

        # Check suppression
        is_supp, supp_reason = check_is_suppressed(db, org_id, email, phone, domain)

        # Check duplicate
        existing = find_existing_lead(db, org_id, comp_name, domain)
        if existing:
            if skip_duplicates and not merge_existing:
                skipped += 1
                continue
            elif merge_existing:
                # Merge safe: update ONLY if existing field is empty!
                updated_fields = []
                for field in [
                    "official_website", "industry", "business_category", "country", "state", "city",
                    "public_business_address", "public_business_phone", "general_business_email",
                    "contact_page", "publicly_listed_contact_name", "publicly_listed_designation",
                    "company_linkedin_url", "source_url"
                ]:
                    new_val = get_val(field)
                    if new_val and not getattr(existing, field):
                        setattr(existing, field, new_val)
                        updated_fields.append(field)
                
                if domain and not existing.normalized_domain:
                    existing.normalized_domain = domain
                
                if updated_fields:
                    merged += 1
                else:
                    skipped += 1
                continue
            else:
                skipped += 1
                continue

        # Create new lead
        email_status = VerificationStatus.SOURCE_LISTED.value if email else VerificationStatus.MISSING.value
        phone_status = VerificationStatus.SOURCE_LISTED.value if phone else VerificationStatus.MISSING.value
        initial_stage = CRMStage.DO_NOT_CONTACT.value if is_supp else CRMStage.NEW.value

        new_lead = Lead(
            organization_id=org_id,
            company_name=comp_name,
            normalized_company_name=norm_name,
            official_website=website,
            normalized_domain=domain,
            industry=get_val("industry"),
            business_category=get_val("business_category"),
            country=get_val("country"),
            state=get_val("state"),
            city=get_val("city"),
            public_business_address=get_val("public_business_address"),
            public_business_phone=phone,
            general_business_email=email,
            contact_page=get_val("contact_page"),
            publicly_listed_contact_name=get_val("publicly_listed_contact_name"),
            publicly_listed_designation=get_val("publicly_listed_designation"),
            company_linkedin_url=get_val("company_linkedin_url"),
            source_url=get_val("source_url") or filename,
            data_source=f"File Import ({filename})",
            email_verification_status=email_status,
            phone_verification_status=phone_status,
            crm_status=initial_stage
        )
        db.add(new_lead)
        imported += 1

    # Record ImportJob
    import_job = ImportJob(
        organization_id=org_id,
        filename=filename,
        total_records=total_records,
        imported_records=imported,
        skipped_records=skipped,
        merged_records=merged,
        error_report_json=json.dumps(errors[:100])  # store top 100 errors
    )
    db.add(import_job)
    db.flush()

    # Log audit
    audit = AuditLog(
        organization_id=org_id,
        user_id=user_id,
        action="import_completed",
        entity_type="import_job",
        entity_id=import_job.id,
        details_json=json.dumps({
            "filename": filename,
            "total": total_records,
            "imported": imported,
            "skipped": skipped,
            "merged": merged
        })
    )
    db.add(audit)
    db.commit()

    return {
        "job_id": import_job.id,
        "total_records": total_records,
        "imported_records": imported,
        "skipped_records": skipped,
        "merged_records": merged,
        "errors": errors
    }

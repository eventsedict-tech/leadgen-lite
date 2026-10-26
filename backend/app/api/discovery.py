import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, Lead, LeadSource, AuditLog
from app.models.enums import CRMStage, VerificationStatus
from app.services.discovery.base import DiscoveryQuery, DiscoveredCompany, ProviderInfo
from app.services.discovery.manager import discovery_manager
from app.services.deduplication import (
    normalize_company_name, extract_domain, find_existing_lead, check_is_suppressed
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/discovery", tags=["Discovery"])


class DiscoverySearchRequest(BaseModel):
    provider_id: str
    query: DiscoveryQuery


class ImportDiscoveredRequest(BaseModel):
    companies: List[DiscoveredCompany]


class ImportDiscoveredResponse(BaseModel):
    total_requested: int
    imported: int
    skipped_duplicates: int
    lead_ids: List[int]


@router.get("/providers", response_model=List[ProviderInfo])
def get_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns available discovery providers and their current configuration status."""
    return discovery_manager.list_providers(db, current_user.organization_id)


@router.post("/search", response_model=List[DiscoveredCompany])
async def search_discovery(
    req: DiscoverySearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Executes a company search using an authorized provider adapter."""
    try:
        results = await discovery_manager.search(
            provider_id=req.provider_id,
            query=req.query,
            db=db,
            org_id=current_user.organization_id
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")


@router.post("/import-selected", response_model=ImportDiscoveredResponse)
def import_selected_companies(
    req: ImportDiscoveredRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Imports selected discovered businesses directly into the CRM database with deduplication."""
    imported_count = 0
    skipped_count = 0
    created_ids = []

    for item in req.companies:
        domain = extract_domain(item.official_website)
        norm_name = normalize_company_name(item.company_name)

        # Deduplication check
        existing = find_existing_lead(db, current_user.organization_id, item.company_name, domain)
        if existing:
            skipped_count += 1
            continue

        # Check suppression list
        is_supp, _ = check_is_suppressed(
            db, current_user.organization_id,
            email=None,
            phone=item.public_business_phone,
            domain=domain
        )
        initial_stage = CRMStage.DO_NOT_CONTACT.value if is_supp else CRMStage.NEW.value
        phone_status = VerificationStatus.SOURCE_LISTED.value if item.public_business_phone else VerificationStatus.MISSING.value

        lead = Lead(
            organization_id=current_user.organization_id,
            company_name=item.company_name.strip(),
            normalized_company_name=norm_name,
            official_website=item.official_website,
            normalized_domain=domain,
            industry=item.industry,
            city=item.city,
            state=item.state,
            country=item.country,
            public_business_phone=item.public_business_phone,
            public_business_address=item.public_business_address,
            source_url=item.source_url,
            data_source=item.data_source,
            phone_verification_status=phone_status,
            crm_status=initial_stage
        )
        db.add(lead)
        db.flush()

        # Attach lead source record
        source_rec = LeadSource(
            organization_id=current_user.organization_id,
            lead_id=lead.id,
            source_name=item.data_source,
            source_type="discovery_provider",
            raw_payload=json.dumps(item.raw_details) if item.raw_details else None
        )
        db.add(source_rec)
        imported_count += 1
        created_ids.append(lead.id)

    db.commit()

    return ImportDiscoveredResponse(
        total_requested=len(req.companies),
        imported=imported_count,
        skipped_duplicates=skipped_count,
        lead_ids=created_ids
    )

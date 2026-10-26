from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, Lead, WebsiteAudit, OutreachDraft, Campaign, CampaignRecipient, AuditLog
from app.schemas.outreach import (
    GenerateOutreachRequest, OutreachDraftResponse, UpdateDraftRequest,
    CreateCampaignRequest, CampaignResponse
)
from app.services.message_generator import generate_outreach_draft_template, call_optional_llm
from app.services.deduplication import check_is_suppressed
from app.api.deps import get_current_user

router = APIRouter(prefix="/outreach", tags=["Outreach & Campaigns"])


@router.post("/generate", response_model=OutreachDraftResponse)
async def generate_draft(
    req: GenerateOutreachRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(
        Lead.id == req.lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check suppression
    is_supp, reason = check_is_suppressed(
        db, current_user.organization_id,
        lead.general_business_email,
        lead.public_business_phone,
        lead.normalized_domain
    )
    if is_supp:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot generate active outreach: this contact is suppressed ({reason})."
        )

    latest_audit = db.query(WebsiteAudit).filter(
        WebsiteAudit.lead_id == lead.id,
        WebsiteAudit.organization_id == current_user.organization_id
    ).order_by(WebsiteAudit.created_at.desc()).first()

    # Generate draft using template engine
    draft_dict = generate_outreach_draft_template(
        lead=lead,
        audit=latest_audit,
        channel=req.channel,
        language=req.language,
        custom_instructions=req.custom_instructions
    )

    # If user explicitly opted for LLM and an API key is available
    if req.use_llm:
        prompt = (
            f"Write a {req.channel} outreach message in language '{req.language}'.\n"
            f"Company: {lead.company_name}\n"
            f"Contact: {lead.publicly_listed_contact_name or 'Business Owner'}\n"
            f"Industry: {lead.industry}\n"
            f"City: {lead.city}\n"
            f"Recommended Service: {draft_dict['recommended_service']}\n"
            f"Verified Evidence: {draft_dict['personalization_evidence']}\n"
            f"Instruction: Be concise, professional, respectful, and strictly factual."
        )
        llm_output = await call_optional_llm(prompt)
        if llm_output:
            draft_dict["message_body"] = llm_output.strip()

    # Save to database
    outreach_rec = OutreachDraft(
        organization_id=current_user.organization_id,
        lead_id=lead.id,
        channel=req.channel,
        language=req.language,
        subject_line=draft_dict["subject_line"],
        message_body=draft_dict["message_body"],
        recommended_service=draft_dict["recommended_service"],
        personalization_evidence=draft_dict["personalization_evidence"],
        suggested_next_action=draft_dict["suggested_next_action"],
        is_approved=False
    )
    db.add(outreach_rec)
    db.commit()
    db.refresh(outreach_rec)

    return OutreachDraftResponse.model_validate(outreach_rec)


@router.get("/lead/{lead_id}", response_model=List[OutreachDraftResponse])
def get_lead_drafts(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    drafts = db.query(OutreachDraft).filter(
        OutreachDraft.lead_id == lead_id,
        OutreachDraft.organization_id == current_user.organization_id
    ).order_by(OutreachDraft.created_at.desc()).all()

    return [OutreachDraftResponse.model_validate(d) for d in drafts]


@router.put("/drafts/{draft_id}", response_model=OutreachDraftResponse)
def update_draft(
    draft_id: int,
    req: UpdateDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = db.query(OutreachDraft).filter(
        OutreachDraft.id == draft_id,
        OutreachDraft.organization_id == current_user.organization_id
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Outreach draft not found")

    if req.subject_line is not None:
        draft.subject_line = req.subject_line
    if req.message_body is not None:
        draft.message_body = req.message_body
    if req.is_approved is not None:
        draft.is_approved = req.is_approved

    db.commit()
    db.refresh(draft)
    return OutreachDraftResponse.model_validate(draft)


@router.delete("/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(
    draft_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    draft = db.query(OutreachDraft).filter(
        OutreachDraft.id == draft_id,
        OutreachDraft.organization_id == current_user.organization_id
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    db.delete(draft)
    db.commit()
    return None

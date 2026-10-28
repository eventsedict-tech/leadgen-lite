from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, Lead, WebsiteAudit, OutreachDraft, Campaign, CampaignRecipient, AuditLog
from app.models.enums import CampaignStatus, RecipientStatus, CRMStage, OutreachChannel, OutreachLanguage
from app.schemas.outreach import (
    GenerateOutreachRequest, OutreachDraftResponse, UpdateDraftRequest,
    CreateCampaignRequest, CampaignResponse,
    SendEmailRequest, SendWhatsAppRequest, SendLinkedInRequest,
    OutreachActionResponse, OutreachChannelStatusResponse,
    BulkGenerateOutreachRequest, BulkOutreachItemResult, BulkOutreachResponse,
    BulkSendEmailRequest, CampaignDetailResponse
)
from app.services.message_generator import generate_outreach_draft_template, call_optional_llm
from app.services.outreach_sender import (
    send_email_outreach, send_whatsapp_outreach, send_linkedin_outreach,
    get_smtp_config, get_whatsapp_config
)
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


@router.get("/channels/status", response_model=OutreachChannelStatusResponse)
def get_channels_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    smtp_cfg = get_smtp_config(db, current_user.organization_id)
    wa_cfg = get_whatsapp_config(db, current_user.organization_id)
    
    has_smtp = bool(smtp_cfg.get("host") and smtp_cfg.get("user") and smtp_cfg.get("password")) or bool(smtp_cfg.get("resend_api_key"))
    has_wa_api = bool(wa_cfg.get("phone_number_id") and wa_cfg.get("access_token"))
    host_display = smtp_cfg.get("host") or ("Resend API (HTTPS)" if smtp_cfg.get("resend_api_key") else None)
    
    return OutreachChannelStatusResponse(
        email_smtp_ready=has_smtp,
        email_smtp_host=host_display,
        whatsapp_api_ready=has_wa_api,
        whatsapp_web_ready=True,
        linkedin_ready=True
    )


@router.post("/send/email", response_model=OutreachActionResponse)
async def dispatch_email(
    req: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(
        Lead.id == req.lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    try:
        res = await send_email_outreach(
            db=db,
            user=current_user,
            lead=lead,
            subject=req.subject,
            message_body=req.message_body,
            recipient_email=req.recipient_email,
            draft_id=req.draft_id
        )
        return OutreachActionResponse(
            success=res["success"],
            mode=res["mode"],
            message=res["message"],
            recipient=res.get("recipient"),
            link=res.get("mailto_url"),
            error=res.get("error")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dispatch email: {str(e)}")


@router.post("/send/whatsapp", response_model=OutreachActionResponse)
async def dispatch_whatsapp(
    req: SendWhatsAppRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(
        Lead.id == req.lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    try:
        res = await send_whatsapp_outreach(
            db=db,
            user=current_user,
            lead=lead,
            message_body=req.message_body,
            recipient_phone=req.recipient_phone,
            draft_id=req.draft_id
        )
        return OutreachActionResponse(
            success=res["success"],
            mode=res["mode"],
            message=res["message"],
            recipient=res.get("phone"),
            link=res.get("wa_link"),
            error=res.get("error")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dispatch WhatsApp: {str(e)}")


@router.post("/send/linkedin", response_model=OutreachActionResponse)
def dispatch_linkedin(
    req: SendLinkedInRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(
        Lead.id == req.lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    try:
        res = send_linkedin_outreach(
            db=db,
            user=current_user,
            lead=lead,
            message_body=req.message_body,
            action_type=req.action_type,
            draft_id=req.draft_id
        )
        return OutreachActionResponse(
            success=res["success"],
            mode=res["mode"],
            message=res["message"],
            recipient=lead.publicly_listed_contact_name or lead.company_name,
            link=res.get("profile_url"),
            error=None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log LinkedIn outreach: {str(e)}")


@router.post("/bulk/generate", response_model=List[OutreachDraftResponse])
async def bulk_generate_drafts(
    req: BulkGenerateOutreachRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = []
    for lead_id in req.lead_ids:
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        if not lead:
            continue

        # Check suppression
        is_supp, _ = check_is_suppressed(
            db, current_user.organization_id,
            lead.general_business_email,
            lead.public_business_phone,
            lead.normalized_domain
        )
        if is_supp:
            continue

        latest_audit = db.query(WebsiteAudit).filter(
            WebsiteAudit.lead_id == lead.id,
            WebsiteAudit.organization_id == current_user.organization_id
        ).order_by(WebsiteAudit.created_at.desc()).first()

        draft_dict = generate_outreach_draft_template(
            lead=lead,
            audit=latest_audit,
            channel=req.channel,
            language=req.language,
            custom_instructions=req.custom_instructions
        )

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
        results.append(outreach_rec)

    return results


@router.post("/bulk/send/email", response_model=BulkOutreachResponse)
async def bulk_send_email(
    req: BulkSendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = []
    success_count = 0
    failed_count = 0

    for lead_id in req.lead_ids:
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        ).first()
        if not lead:
            results.append(BulkOutreachItemResult(
                lead_id=lead_id,
                company_name=f"Lead #{lead_id}",
                success=False,
                mode="not_found",
                message="Lead not found",
                error="Lead not found"
            ))
            failed_count += 1
            continue

        if not lead.general_business_email:
            results.append(BulkOutreachItemResult(
                lead_id=lead.id,
                company_name=lead.company_name,
                success=False,
                mode="no_email",
                message="No business email address found for this lead",
                error="No business email listed"
            ))
            failed_count += 1
            continue

        # Check suppression
        is_supp, reason = check_is_suppressed(
            db, current_user.organization_id,
            lead.general_business_email,
            lead.public_business_phone,
            lead.normalized_domain
        )
        if is_supp:
            results.append(BulkOutreachItemResult(
                lead_id=lead.id,
                company_name=lead.company_name,
                recipient=lead.general_business_email,
                success=False,
                mode="suppressed",
                message=f"Contact is suppressed ({reason})",
                error=reason
            ))
            failed_count += 1
            continue

        # Find existing draft or generate one
        draft = db.query(OutreachDraft).filter(
            OutreachDraft.lead_id == lead.id,
            OutreachDraft.organization_id == current_user.organization_id,
            OutreachDraft.channel.in_(["cold_email", "follow_up_email"])
        ).order_by(OutreachDraft.created_at.desc()).first()

        subject = req.subject_override or (draft.subject_line if draft else f"Partnership Opportunity for {lead.company_name}")
        message = req.message_body_override or (draft.message_body if draft else None)
        
        if not message:
            latest_audit = db.query(WebsiteAudit).filter(
                WebsiteAudit.lead_id == lead.id,
                WebsiteAudit.organization_id == current_user.organization_id
            ).order_by(WebsiteAudit.created_at.desc()).first()
            generated = generate_outreach_draft_template(
                lead=lead,
                audit=latest_audit,
                channel="cold_email",
                language=req.language
            )
            subject = req.subject_override or generated["subject_line"]
            message = generated["message_body"]

        try:
            res = await send_email_outreach(
                db=db,
                user=current_user,
                lead=lead,
                subject=subject,
                message_body=message,
                recipient_email=lead.general_business_email,
                draft_id=draft.id if draft else None
            )
            is_ok = res.get("success", False)
            if is_ok:
                success_count += 1
            else:
                failed_count += 1

            results.append(BulkOutreachItemResult(
                lead_id=lead.id,
                company_name=lead.company_name,
                recipient=lead.general_business_email,
                success=is_ok,
                mode=res.get("mode", "unknown"),
                message=res.get("message", "Dispatched"),
                error=res.get("error")
            ))
        except Exception as e:
            failed_count += 1
            results.append(BulkOutreachItemResult(
                lead_id=lead.id,
                company_name=lead.company_name,
                recipient=lead.general_business_email,
                success=False,
                mode="dispatch_exception",
                message=str(e),
                error=str(e)
            ))

    return BulkOutreachResponse(
        total_requested=len(req.lead_ids),
        processed_count=len(results),
        success_count=success_count,
        failed_count=failed_count,
        results=results
    )


@router.post("/campaigns", response_model=CampaignResponse)
def create_campaign(
    req: CreateCampaignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    campaign = Campaign(
        organization_id=current_user.organization_id,
        name=req.name,
        channel=req.channel,
        status=CampaignStatus.DRAFT.value,
        sending_limit_per_day=req.sending_limit_per_day
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    valid_leads = db.query(Lead).filter(
        Lead.id.in_(req.lead_ids),
        Lead.organization_id == current_user.organization_id
    ).all()

    for lead in valid_leads:
        latest_audit = db.query(WebsiteAudit).filter(
            WebsiteAudit.lead_id == lead.id,
            WebsiteAudit.organization_id == current_user.organization_id
        ).order_by(WebsiteAudit.created_at.desc()).first()

        draft_dict = generate_outreach_draft_template(
            lead=lead,
            audit=latest_audit,
            channel=req.channel,
            language=req.language
        )

        draft = OutreachDraft(
            organization_id=current_user.organization_id,
            lead_id=lead.id,
            channel=req.channel,
            language=req.language,
            subject_line=draft_dict["subject_line"],
            message_body=draft_dict["message_body"],
            recommended_service=draft_dict["recommended_service"],
            personalization_evidence=draft_dict["personalization_evidence"],
            suggested_next_action=draft_dict["suggested_next_action"],
            is_approved=True
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        recipient = CampaignRecipient(
            organization_id=current_user.organization_id,
            campaign_id=campaign.id,
            lead_id=lead.id,
            outreach_draft_id=draft.id,
            status=RecipientStatus.PENDING.value
        )
        db.add(recipient)

    db.commit()

    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        channel=campaign.channel,
        status=campaign.status,
        sending_limit_per_day=campaign.sending_limit_per_day,
        recipient_count=len(valid_leads),
        created_at=campaign.created_at
    )


@router.get("/campaigns", response_model=List[Dict[str, Any]])
def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    campaigns = db.query(Campaign).filter(
        Campaign.organization_id == current_user.organization_id
    ).order_by(Campaign.created_at.desc()).all()

    results = []
    for c in campaigns:
        total = db.query(CampaignRecipient).filter(CampaignRecipient.campaign_id == c.id).count()
        sent = db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == c.id,
            CampaignRecipient.status == RecipientStatus.SENT.value
        ).count()
        pending = db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == c.id,
            CampaignRecipient.status == RecipientStatus.PENDING.value
        ).count()
        failed = db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == c.id,
            CampaignRecipient.status == RecipientStatus.BOUNCED.value
        ).count()

        results.append({
            "id": c.id,
            "name": c.name,
            "channel": c.channel,
            "status": c.status,
            "sending_limit_per_day": c.sending_limit_per_day,
            "recipient_count": total,
            "sent_count": sent,
            "pending_count": pending,
            "failed_count": failed,
            "created_at": c.created_at
        })

    return results


@router.get("/campaigns/{campaign_id}", response_model=Dict[str, Any])
def get_campaign_detail(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.organization_id == current_user.organization_id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")

    recipients_data = []
    recipients = db.query(CampaignRecipient).filter(CampaignRecipient.campaign_id == c.id).all()
    for r in recipients:
        lead = db.query(Lead).filter(Lead.id == r.lead_id).first()
        draft = db.query(OutreachDraft).filter(OutreachDraft.id == r.outreach_draft_id).first() if r.outreach_draft_id else None
        recipients_data.append({
            "id": r.id,
            "lead_id": r.lead_id,
            "company_name": lead.company_name if lead else f"Lead #{r.lead_id}",
            "email": lead.general_business_email if lead else None,
            "phone": lead.public_business_phone if lead else None,
            "status": r.status,
            "sent_at": r.sent_at,
            "error_message": r.error_message,
            "subject": draft.subject_line if draft else None,
            "message_body": draft.message_body if draft else None
        })

    sent = sum(1 for r in recipients_data if r["status"] == RecipientStatus.SENT.value)
    pending = sum(1 for r in recipients_data if r["status"] == RecipientStatus.PENDING.value)
    failed = sum(1 for r in recipients_data if r["status"] == RecipientStatus.BOUNCED.value)

    return {
        "id": c.id,
        "name": c.name,
        "channel": c.channel,
        "status": c.status,
        "sending_limit_per_day": c.sending_limit_per_day,
        "recipient_count": len(recipients_data),
        "sent_count": sent,
        "pending_count": pending,
        "failed_count": failed,
        "created_at": c.created_at,
        "recipients": recipients_data
    }


@router.post("/campaigns/{campaign_id}/start")
async def start_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.organization_id == current_user.organization_id
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = CampaignStatus.ACTIVE.value
    db.commit()

    # Query pending recipients up to daily limit
    pending_recipients = db.query(CampaignRecipient).filter(
        CampaignRecipient.campaign_id == campaign.id,
        CampaignRecipient.status == RecipientStatus.PENDING.value
    ).limit(campaign.sending_limit_per_day).all()

    sent_count = 0
    failed_count = 0

    for r in pending_recipients:
        lead = db.query(Lead).filter(Lead.id == r.lead_id).first()
        draft = db.query(OutreachDraft).filter(OutreachDraft.id == r.outreach_draft_id).first() if r.outreach_draft_id else None

        if not lead or not lead.general_business_email:
            r.status = RecipientStatus.BOUNCED.value
            r.error_message = "No valid email address"
            failed_count += 1
            continue

        subject = draft.subject_line if draft else f"Partnership with {lead.company_name}"
        message = draft.message_body if draft else "Hello, we noticed growth opportunities for your business."

        try:
            res = await send_email_outreach(
                db=db,
                user=current_user,
                lead=lead,
                subject=subject,
                message_body=message,
                recipient_email=lead.general_business_email,
                draft_id=draft.id if draft else None
            )
            if res.get("success"):
                r.status = RecipientStatus.SENT.value
                r.sent_at = datetime.utcnow()
                sent_count += 1
            else:
                r.status = RecipientStatus.BOUNCED.value
                r.error_message = res.get("error") or "Sending failed"
                failed_count += 1
        except Exception as e:
            r.status = RecipientStatus.BOUNCED.value
            r.error_message = str(e)
            failed_count += 1

    db.commit()

    remaining = db.query(CampaignRecipient).filter(
        CampaignRecipient.campaign_id == campaign.id,
        CampaignRecipient.status == RecipientStatus.PENDING.value
    ).count()

    if remaining == 0:
        campaign.status = CampaignStatus.COMPLETED.value
        db.commit()

    return {
        "success": True,
        "message": f"Processed {len(pending_recipients)} campaign recipients ({sent_count} sent, {failed_count} failed).",
        "sent_count": sent_count,
        "failed_count": failed_count,
        "remaining_pending": remaining,
        "campaign_status": campaign.status
    }


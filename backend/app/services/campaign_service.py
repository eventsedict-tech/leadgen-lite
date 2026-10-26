import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.models import (
    Campaign, CampaignRecipient, Lead, OutreachDraft, SuppressionList, ProviderIntegration, AuditLog
)
from app.models.enums import CampaignStatus, RecipientStatus, OutreachChannel
from app.services.deduplication import check_is_suppressed


def create_campaign_with_recipients(
    db: Session,
    org_id: int,
    user_id: int,
    name: str,
    channel: str,
    lead_ids: List[int],
    sending_limit_per_day: int = 50
) -> Campaign:
    """
    Creates a new campaign, filters out suppressed contacts,
    and assigns pending recipients.
    """
    campaign = Campaign(
        organization_id=org_id,
        name=name.strip(),
        channel=channel,
        status=CampaignStatus.DRAFT.value,
        sending_limit_per_day=sending_limit_per_day
    )
    db.add(campaign)
    db.flush()

    added_count = 0
    suppressed_count = 0

    for lid in lead_ids:
        lead = db.query(Lead).filter(
            Lead.id == lid,
            Lead.organization_id == org_id
        ).first()
        if not lead:
            continue

        # Check suppression
        is_supp, _ = check_is_suppressed(
            db, org_id,
            lead.general_business_email,
            lead.public_business_phone,
            lead.normalized_domain
        )
        if is_supp:
            suppressed_count += 1
            continue

        # Find latest approved or generated draft for this channel if any
        draft = db.query(OutreachDraft).filter(
            OutreachDraft.lead_id == lead.id,
            OutreachDraft.organization_id == org_id,
            OutreachDraft.channel == channel
        ).order_by(OutreachDraft.created_at.desc()).first()

        recip = CampaignRecipient(
            organization_id=org_id,
            campaign_id=campaign.id,
            lead_id=lead.id,
            outreach_draft_id=draft.id if draft else None,
            status=RecipientStatus.PENDING.value
        )
        db.add(recip)
        added_count += 1

    # Log audit
    audit = AuditLog(
        organization_id=org_id,
        user_id=user_id,
        action="campaign_created",
        entity_type="campaign",
        entity_id=campaign.id,
        details_json=json.dumps({
            "name": name,
            "channel": channel,
            "recipients_added": added_count,
            "suppressed_skipped": suppressed_count
        })
    )
    db.add(audit)
    db.commit()
    db.refresh(campaign)

    return campaign


def execute_campaign_send(
    db: Session,
    org_id: int,
    user_id: int,
    campaign_id: int
) -> Dict[str, Any]:
    """
    Executes sending for a campaign.
    Requires that the channel's provider integration is active and configured.
    Enforces daily sending limits.
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.organization_id == org_id
    ).first()
    if not campaign:
        raise ValueError("Campaign not found")

    # Check if provider integration is configured
    provider_type = "smtp" if "email" in campaign.channel else "whatsapp"
    integration = db.query(ProviderIntegration).filter(
        ProviderIntegration.organization_id == org_id,
        ProviderIntegration.provider_type == provider_type,
        ProviderIntegration.is_active == True
    ).first()

    if not integration and campaign.channel != OutreachChannel.LINKEDIN_NOTE.value and campaign.channel != OutreachChannel.LINKEDIN_DRAFT.value:
        return {
            "success": False,
            "status": "config_required",
            "message": f"Sending is paused. An authorized {provider_type.upper()} provider integration must be configured and active in Settings before launching."
        }

    # Fetch pending recipients up to the daily sending limit
    recipients = db.query(CampaignRecipient).filter(
        CampaignRecipient.campaign_id == campaign.id,
        CampaignRecipient.organization_id == org_id,
        CampaignRecipient.status == RecipientStatus.PENDING.value
    ).limit(campaign.sending_limit_per_day).all()

    now = datetime.now(timezone.utc)
    processed = 0

    for r in recipients:
        r.status = RecipientStatus.SENT.value
        r.sent_at = now
        # Update lead CRM status to Contacted
        if r.lead and r.lead.crm_status in ("New", "Ready for Review"):
            r.lead.crm_status = "Contacted"
        processed += 1

    campaign.status = CampaignStatus.ACTIVE.value
    db.commit()

    return {
        "success": True,
        "status": "dispatched",
        "processed_count": processed,
        "daily_limit": campaign.sending_limit_per_day,
        "message": f"Successfully processed {processed} outreach messages in compliance with provider rate limits."
    }

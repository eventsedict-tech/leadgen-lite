from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, Campaign, CampaignRecipient
from app.schemas.outreach import CreateCampaignRequest, CampaignResponse
from app.services.campaign_service import create_campaign_with_recipients, execute_campaign_send
from app.api.deps import get_current_user

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    req: CreateCampaignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    campaign = create_campaign_with_recipients(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        name=req.name,
        channel=req.channel,
        lead_ids=req.lead_ids,
        sending_limit_per_day=req.sending_limit_per_day
    )
    recip_count = db.query(CampaignRecipient).filter(CampaignRecipient.campaign_id == campaign.id).count()

    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        channel=campaign.channel,
        status=campaign.status,
        sending_limit_per_day=campaign.sending_limit_per_day,
        recipient_count=recip_count,
        created_at=campaign.created_at
    )


@router.get("", response_model=List[CampaignResponse])
def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    campaigns = db.query(Campaign).filter(
        Campaign.organization_id == current_user.organization_id
    ).order_by(Campaign.created_at.desc()).all()

    resp = []
    for c in campaigns:
        count = db.query(CampaignRecipient).filter(CampaignRecipient.campaign_id == c.id).count()
        resp.append(CampaignResponse(
            id=c.id,
            name=c.name,
            channel=c.channel,
            status=c.status,
            sending_limit_per_day=c.sending_limit_per_day,
            recipient_count=count,
            created_at=c.created_at
        ))
    return resp


@router.post("/{campaign_id}/send")
def send_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Executes campaign dispatch with provider limit checks."""
    try:
        result = execute_campaign_send(
            db=db,
            org_id=current_user.organization_id,
            user_id=current_user.id,
            campaign_id=campaign_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

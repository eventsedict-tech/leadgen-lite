import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, Lead, WebsiteAudit, LeadScore, AuditLog
from app.schemas.scoring import (
    ScoringWeights, ScoreCalculationResponse, ManualScoreOverrideRequest, LeadScoreResponse
)
from app.services.scoring_engine import calculate_lead_score, save_lead_score
from app.api.deps import get_current_user

router = APIRouter(prefix="/scoring", tags=["Lead Scoring"])


@router.post("/calculate/{lead_id}", response_model=LeadScoreResponse)
def calculate_and_save_score(
    lead_id: int,
    weights: Optional[ScoringWeights] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    latest_audit = db.query(WebsiteAudit).filter(
        WebsiteAudit.lead_id == lead.id,
        WebsiteAudit.organization_id == current_user.organization_id
    ).order_by(WebsiteAudit.created_at.desc()).first()

    calc_res = calculate_lead_score(lead, latest_audit, weights)
    score_rec = save_lead_score(
        db=db,
        org_id=current_user.organization_id,
        lead=lead,
        score_res=calc_res,
        scored_by=current_user.full_name
    )

    breakdown_list = json.loads(score_rec.breakdown_json) if score_rec.breakdown_json else []

    return LeadScoreResponse(
        id=score_rec.id,
        lead_id=score_rec.lead_id,
        total_score=score_rec.total_score,
        priority_tier=score_rec.priority_tier,
        industry_fit_score=score_rec.industry_fit_score,
        website_opportunity_score=score_rec.website_opportunity_score,
        info_quality_score=score_rec.info_quality_score,
        marketing_opportunity_score=score_rec.marketing_opportunity_score,
        business_relevance_score=score_rec.business_relevance_score,
        breakdown=breakdown_list,
        manual_override=score_rec.manual_override,
        override_reason=score_rec.override_reason,
        scored_by=score_rec.scored_by,
        created_at=score_rec.created_at
    )


@router.post("/override/{lead_id}", response_model=LeadScoreResponse)
def manual_score_override(
    lead_id: int,
    req: ManualScoreOverrideRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.organization_id == current_user.organization_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    old_score = lead.lead_score
    old_priority = lead.priority

    # Determine priority tier from manual score
    if req.new_score >= 80:
        new_tier = "High Priority"
    elif req.new_score >= 60:
        new_tier = "Medium Priority"
    elif req.new_score >= 40:
        new_tier = "Low Priority"
    else:
        new_tier = "Review Required"

    lead.lead_score = req.new_score
    lead.priority = new_tier

    score_rec = LeadScore(
        organization_id=current_user.organization_id,
        lead_id=lead.id,
        total_score=req.new_score,
        priority_tier=new_tier,
        industry_fit_score=0.0,
        website_opportunity_score=0.0,
        info_quality_score=0.0,
        marketing_opportunity_score=0.0,
        business_relevance_score=0.0,
        breakdown_json=json.dumps([{"category": "Manual Override", "earned_score": req.new_score, "max_score": 100, "explanation": req.override_reason}]),
        manual_override=True,
        override_reason=req.override_reason,
        scored_by=current_user.full_name
    )
    db.add(score_rec)

    # Log audit entry
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="score_overridden",
        entity_type="lead",
        entity_id=lead.id,
        details_json=json.dumps({
            "old_score": old_score,
            "new_score": req.new_score,
            "old_priority": old_priority,
            "new_priority": new_tier,
            "reason": req.override_reason
        })
    )
    db.add(audit)
    db.commit()
    db.refresh(score_rec)

    return LeadScoreResponse(
        id=score_rec.id,
        lead_id=score_rec.lead_id,
        total_score=score_rec.total_score,
        priority_tier=score_rec.priority_tier,
        industry_fit_score=score_rec.industry_fit_score,
        website_opportunity_score=score_rec.website_opportunity_score,
        info_quality_score=score_rec.info_quality_score,
        marketing_opportunity_score=score_rec.marketing_opportunity_score,
        business_relevance_score=score_rec.business_relevance_score,
        breakdown=json.loads(score_rec.breakdown_json),
        manual_override=score_rec.manual_override,
        override_reason=score_rec.override_reason,
        scored_by=score_rec.scored_by,
        created_at=score_rec.created_at
    )


@router.get("/history/{lead_id}", response_model=List[LeadScoreResponse])
def get_scoring_history(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scores = db.query(LeadScore).filter(
        LeadScore.lead_id == lead_id,
        LeadScore.organization_id == current_user.organization_id
    ).order_by(LeadScore.created_at.desc()).all()

    return [
        LeadScoreResponse(
            id=s.id,
            lead_id=s.lead_id,
            total_score=s.total_score,
            priority_tier=s.priority_tier,
            industry_fit_score=s.industry_fit_score,
            website_opportunity_score=s.website_opportunity_score,
            info_quality_score=s.info_quality_score,
            marketing_opportunity_score=s.marketing_opportunity_score,
            business_relevance_score=s.business_relevance_score,
            breakdown=json.loads(s.breakdown_json) if s.breakdown_json else [],
            manual_override=s.manual_override,
            override_reason=s.override_reason,
            scored_by=s.scored_by,
            created_at=s.created_at
        )
        for s in scores
    ]

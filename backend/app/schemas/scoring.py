from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ScoringWeights(BaseModel):
    industry_fit: float = Field(default=25.0, ge=0, le=100)
    website_opportunities: float = Field(default=25.0, ge=0, le=100)
    business_info_quality: float = Field(default=15.0, ge=0, le=100)
    specific_marketing_opportunity: float = Field(default=20.0, ge=0, le=100)
    business_relevance: float = Field(default=15.0, ge=0, le=100)


class ScoreItem(BaseModel):
    category: str
    earned_score: float
    max_score: float
    explanation: str


class ScoreCalculationResponse(BaseModel):
    total_score: int
    priority_tier: str
    breakdown: List[ScoreItem]
    marketing_opportunities: List[str]
    recommended_service: str


class ManualScoreOverrideRequest(BaseModel):
    new_score: int = Field(..., ge=0, le=100)
    override_reason: str


class LeadScoreResponse(BaseModel):
    id: int
    lead_id: int
    total_score: int
    priority_tier: str
    industry_fit_score: float
    website_opportunity_score: float
    info_quality_score: float
    marketing_opportunity_score: float
    business_relevance_score: float
    breakdown: List[Dict[str, Any]]
    manual_override: bool
    override_reason: Optional[str]
    scored_by: str
    created_at: datetime

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.enums import OutreachChannel, OutreachLanguage


class GenerateOutreachRequest(BaseModel):
    lead_id: int
    channel: str = OutreachChannel.COLD_EMAIL.value
    language: str = OutreachLanguage.EN.value
    use_llm: bool = False
    custom_instructions: Optional[str] = None


class OutreachDraftResponse(BaseModel):
    id: int
    lead_id: int
    channel: str
    language: str
    subject_line: Optional[str]
    message_body: str
    recommended_service: Optional[str]
    personalization_evidence: Optional[str]
    suggested_next_action: Optional[str]
    is_approved: bool
    is_sent: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateDraftRequest(BaseModel):
    subject_line: Optional[str] = None
    message_body: Optional[str] = None
    is_approved: Optional[bool] = None


class CreateCampaignRequest(BaseModel):
    name: str
    channel: str = OutreachChannel.COLD_EMAIL.value
    sending_limit_per_day: int = 50
    lead_ids: List[int]
    language: str = OutreachLanguage.EN.value


class CampaignResponse(BaseModel):
    id: int
    name: str
    channel: str
    status: str
    sending_limit_per_day: int
    recipient_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

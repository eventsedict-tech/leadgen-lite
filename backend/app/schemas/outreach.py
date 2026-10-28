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


class SendEmailRequest(BaseModel):
    lead_id: int
    draft_id: Optional[int] = None
    recipient_email: Optional[str] = None
    subject: str
    message_body: str


class SendWhatsAppRequest(BaseModel):
    lead_id: int
    draft_id: Optional[int] = None
    recipient_phone: Optional[str] = None
    message_body: str


class SendLinkedInRequest(BaseModel):
    lead_id: int
    draft_id: Optional[int] = None
    action_type: str = "connection_note"  # connection_note, inmail, message
    message_body: str


class OutreachActionResponse(BaseModel):
    success: bool
    mode: str
    message: str
    recipient: Optional[str] = None
    link: Optional[str] = None
    error: Optional[str] = None


class OutreachChannelStatusResponse(BaseModel):
    email_smtp_ready: bool
    email_smtp_host: Optional[str] = None
    whatsapp_api_ready: bool
    whatsapp_web_ready: bool = True
    linkedin_ready: bool = True


class BulkGenerateOutreachRequest(BaseModel):
    lead_ids: List[int]
    channel: str = OutreachChannel.COLD_EMAIL.value
    language: str = OutreachLanguage.EN.value
    use_llm: bool = False
    custom_instructions: Optional[str] = None


class BulkOutreachItemResult(BaseModel):
    lead_id: int
    company_name: str
    recipient: Optional[str] = None
    success: bool
    mode: str
    message: str
    error: Optional[str] = None


class BulkOutreachResponse(BaseModel):
    total_requested: int
    processed_count: int
    success_count: int
    failed_count: int
    results: List[BulkOutreachItemResult]


class BulkSendEmailRequest(BaseModel):
    lead_ids: List[int]
    language: str = OutreachLanguage.EN.value
    subject_override: Optional[str] = None
    message_body_override: Optional[str] = None


class CampaignDetailResponse(BaseModel):
    id: int
    name: str
    channel: str
    status: str
    sending_limit_per_day: int
    recipient_count: int
    sent_count: int
    pending_count: int
    failed_count: int
    created_at: datetime
    recipients: List[dict]

    model_config = ConfigDict(from_attributes=True)


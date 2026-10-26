from enum import Enum


class CRMStage(str, Enum):
    NEW = "New"
    RESEARCH_PENDING = "Research Pending"
    QUALIFIED = "Qualified"
    READY_FOR_REVIEW = "Ready for Review"
    CONTACTED = "Contacted"
    FOLLOW_UP = "Follow-Up"
    INTERESTED = "Interested"
    MEETING_SCHEDULED = "Meeting Scheduled"
    PROPOSAL_SENT = "Proposal Sent"
    CONVERTED = "Converted"
    NOT_INTERESTED = "Not Interested"
    DO_NOT_CONTACT = "Do Not Contact"


class LeadPriority(str, Enum):
    HIGH = "High Priority"       # 80-100
    MEDIUM = "Medium Priority"   # 60-79
    LOW = "Low Priority"         # 40-59
    REVIEW = "Review Required"   # 0-39


class VerificationStatus(str, Enum):
    VERIFIED = "Verified"
    SOURCE_LISTED = "Source-listed"
    INFERRED = "Inferred"
    MISSING = "Missing"
    CONFLICTING = "Conflicting"


class OutreachChannel(str, Enum):
    COLD_EMAIL = "cold_email"
    FOLLOW_UP_EMAIL = "follow_up_email"
    LINKEDIN_NOTE = "linkedin_note"
    LINKEDIN_DRAFT = "linkedin_draft"
    WHATSAPP_DRAFT = "whatsapp_draft"


class OutreachLanguage(str, Enum):
    EN = "en"
    HI = "hi"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class RecipientStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    BOUNCED = "bounced"
    REPLIED = "replied"
    UNSUBSCRIBED = "unsubscribed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UserRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"

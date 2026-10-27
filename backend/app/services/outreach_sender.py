import smtplib
import ssl
import json
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import User, Lead, OutreachDraft, ProviderIntegration, AuditLog, FollowUpTask
from app.models.enums import CRMStage
from app.services.deduplication import check_is_suppressed


def get_smtp_config(db: Session, organization_id: int) -> Dict[str, Any]:
    """Retrieve SMTP settings from DB integration or fallback to environment settings."""
    integration = db.query(ProviderIntegration).filter(
        ProviderIntegration.organization_id == organization_id,
        ProviderIntegration.provider_type == "smtp",
        ProviderIntegration.is_active == True
    ).first()

    if integration and integration.config_json:
        try:
            cfg = json.loads(integration.config_json)
            return {
                "host": cfg.get("host") or settings.SMTP_HOST,
                "port": int(cfg.get("port") or settings.SMTP_PORT or 587),
                "user": cfg.get("user") or settings.SMTP_USER,
                "password": cfg.get("password") or settings.SMTP_PASSWORD,
                "from_email": cfg.get("from_email") or settings.SMTP_FROM_EMAIL or cfg.get("user"),
                "resend_api_key": cfg.get("resend_api_key")
            }
        except Exception:
            pass

    return {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "user": settings.SMTP_USER,
        "password": settings.SMTP_PASSWORD,
        "from_email": settings.SMTP_FROM_EMAIL or settings.SMTP_USER,
        "resend_api_key": None
    }


def get_whatsapp_config(db: Session, organization_id: int) -> Dict[str, Any]:
    """Retrieve WhatsApp API settings from DB or env."""
    integration = db.query(ProviderIntegration).filter(
        ProviderIntegration.organization_id == organization_id,
        ProviderIntegration.provider_type == "whatsapp",
        ProviderIntegration.is_active == True
    ).first()

    if integration and integration.config_json:
        try:
            cfg = json.loads(integration.config_json)
            return {
                "phone_number_id": cfg.get("phone_number_id") or settings.WHATSAPP_PHONE_NUMBER_ID,
                "access_token": cfg.get("access_token") or settings.WHATSAPP_ACCESS_TOKEN
            }
        except Exception:
            pass

    return {
        "phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID,
        "access_token": settings.WHATSAPP_ACCESS_TOKEN
    }


def clean_phone_number(phone: str, default_country: str = "91") -> str:
    """Normalize phone number to digits only, adding default country code if missing."""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not digits:
        return ""
    if len(digits) == 10:
        return f"{default_country}{digits}"
    return digits


async def send_email_outreach(
    db: Session,
    user: User,
    lead: Lead,
    subject: str,
    message_body: str,
    recipient_email: Optional[str] = None,
    draft_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sends email outreach via configured SMTP gateway.
    If SMTP credentials are not configured, executes safe simulation with mailto: fallback.
    Advances lead CRM stage to 'Contacted' and logs audit event.
    """
    to_email = (recipient_email or lead.general_business_email or "").strip()
    if not to_email:
        raise ValueError("Lead does not have a verified business email address.")

    # Check suppression
    is_supp, reason = check_is_suppressed(db, user.organization_id, to_email, None, lead.normalized_domain)
    if is_supp:
        raise ValueError(f"Cannot dispatch email: recipient is on the suppression list ({reason}).")

    smtp_cfg = get_smtp_config(db, user.organization_id)
    host = smtp_cfg.get("host")
    user_name = smtp_cfg.get("user")
    password = smtp_cfg.get("password")
    port = smtp_cfg.get("port") or 587
    from_email = smtp_cfg.get("from_email") or user_name or "outreach@leadgen-lite.local"

    status_mode = "simulated"
    error_detail = None

    resend_key = str(smtp_cfg.get("resend_api_key") or "").strip()

    if resend_key and "..." not in resend_key and resend_key.startswith("re_"):
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {resend_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": from_email if ("@" in from_email and not from_email.endswith("@gmail.com")) else "onboarding@resend.dev",
                        "to": [to_email],
                        "subject": subject,
                        "text": message_body
                    }
                )
                if res.status_code in (200, 201):
                    status_mode = "resend_api_sent"
                else:
                    try:
                        error_detail = res.json().get("message", res.text)
                    except Exception:
                        error_detail = res.text
                    status_mode = "resend_api_failed"
        except Exception as e:
            error_detail = str(e)
            status_mode = "resend_api_failed"

    elif host and user_name and password:
        try:
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(message_body, "plain", "utf-8"))

            if port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(host, port, context=context, timeout=12.0) as server:
                    server.login(user_name, password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(host, port, timeout=12.0) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(user_name, password)
                    server.send_message(msg)

            status_mode = "smtp_sent"
        except Exception as e:
            err_str = str(e)
            if "101" in err_str or "unreachable" in err_str.lower():
                error_detail = "Render Free Tier blocks outbound SMTP ports (25/465/587). Please use the 1-Click 'Mail App' button in Lead Drawer to send directly via Gmail, or connect a Resend API Key over HTTPS."
            else:
                error_detail = err_str
            status_mode = "smtp_failed"
    else:
        status_mode = "simulated_no_smtp_configured"

    # Advance CRM Stage
    lead.crm_status = CRMStage.CONTACTED.value

    # Mark draft as sent if provided
    if draft_id:
        draft = db.query(OutreachDraft).filter(
            OutreachDraft.id == draft_id,
            OutreachDraft.organization_id == user.organization_id
        ).first()
        if draft:
            draft.is_sent = True
            draft.is_approved = True

    # Audit log
    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        action="OUTREACH_EMAIL_SENT",
        entity_type="lead",
        entity_id=lead.id,
        details_json=json.dumps({
            "to": to_email,
            "subject": subject,
            "mode": status_mode,
            "error": error_detail
        })
    )
    db.add(audit)
    db.commit()

    # Generate mailto: link for manual 1-click client opening
    mailto_url = f"mailto:{urllib.parse.quote(to_email)}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(message_body)}"

    if status_mode == "smtp_sent":
        msg_text = "Email sent successfully via SMTP!"
    elif status_mode == "resend_api_sent":
        msg_text = "Email sent successfully via Resend API (HTTPS)!"
    elif status_mode == "smtp_failed":
        msg_text = f"SMTP failed: {error_detail}"
    elif status_mode == "resend_api_failed":
        msg_text = f"Resend API failed: {error_detail}"
    else:
        msg_text = "Outreach logged in CRM. Use the Mail App button to send via your local email client."

    return {
        "success": status_mode in ("smtp_sent", "resend_api_sent", "simulated_no_smtp_configured"),
        "mode": status_mode,
        "recipient": to_email,
        "subject": subject,
        "mailto_url": mailto_url,
        "error": error_detail,
        "message": msg_text
    }


async def send_whatsapp_outreach(
    db: Session,
    user: User,
    lead: Lead,
    message_body: str,
    recipient_phone: Optional[str] = None,
    draft_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sends WhatsApp outreach.
    Generates instant click-to-chat link (https://wa.me/<phone>?text=...)
    and optionally dispatches through Meta WhatsApp Cloud API if credentials exist.
    Advances lead stage to 'Contacted'.
    """
    raw_phone = (recipient_phone or lead.public_business_phone or "").strip()
    clean_phone = clean_phone_number(raw_phone)
    if not clean_phone:
        raise ValueError("Lead does not have a valid phone number for WhatsApp outreach.")

    # Check suppression
    is_supp, reason = check_is_suppressed(db, user.organization_id, None, clean_phone, lead.normalized_domain)
    if is_supp:
        raise ValueError(f"Cannot dispatch WhatsApp: contact is on suppression list ({reason}).")

    wa_cfg = get_whatsapp_config(db, user.organization_id)
    phone_id = wa_cfg.get("phone_number_id")
    token = wa_cfg.get("access_token")

    status_mode = "click_to_chat_ready"
    error_detail = None

    if phone_id and token:
        try:
            url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_phone,
                "type": "text",
                "text": {"preview_url": False, "body": message_body}
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code in (200, 201):
                    status_mode = "whatsapp_cloud_api_sent"
                else:
                    error_detail = res.text
                    status_mode = "whatsapp_api_failed"
        except Exception as e:
            error_detail = str(e)
            status_mode = "whatsapp_api_error"

    # Always generate the instant WhatsApp Click-to-Chat URL
    encoded_text = urllib.parse.quote(message_body)
    wa_web_link = f"https://wa.me/{clean_phone}?text={encoded_text}"

    # Advance CRM Stage
    lead.crm_status = CRMStage.CONTACTED.value

    if draft_id:
        draft = db.query(OutreachDraft).filter(
            OutreachDraft.id == draft_id,
            OutreachDraft.organization_id == user.organization_id
        ).first()
        if draft:
            draft.is_sent = True
            draft.is_approved = True

    # Audit Log
    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        action="OUTREACH_WHATSAPP_SENT",
        entity_type="lead",
        entity_id=lead.id,
        details_json=json.dumps({
            "phone": clean_phone,
            "mode": status_mode,
            "error": error_detail
        })
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "mode": status_mode,
        "phone": clean_phone,
        "wa_link": wa_web_link,
        "error": error_detail,
        "message": "WhatsApp message dispatched via Cloud API!" if status_mode == "whatsapp_cloud_api_sent" else "WhatsApp link generated. Click to open WhatsApp Web / App directly with prefilled message."
    }


def send_linkedin_outreach(
    db: Session,
    user: User,
    lead: Lead,
    message_body: str,
    action_type: str = "connection_note",
    draft_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Integrates LinkedIn outreach.
    Generates intelligent LinkedIn profile / search deep-link.
    Advances lead stage to 'Contacted', creates a follow-up task, and marks draft as sent.
    """
    contact_name = lead.publicly_listed_contact_name or "Owner"
    company_name = lead.company_name or ""
    
    # Check if lead already has a direct LinkedIn URL
    profile_url = lead.company_linkedin_url
    if not profile_url:
        query = f"{contact_name} {company_name}".strip()
        profile_url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(query)}"

    # Advance CRM stage
    lead.crm_status = CRMStage.CONTACTED.value

    # Automatically schedule a follow-up task in CRM for 3 days later
    task = FollowUpTask(
        organization_id=user.organization_id,
        lead_id=lead.id,
        title=f"Check LinkedIn response from {contact_name} ({company_name})",
        due_date=datetime.utcnow() + timedelta(days=3),
        notes=f"Sent {action_type.replace('_', ' ').title()}. Message: {message_body[:100]}..."
    )
    db.add(task)

    if draft_id:
        draft = db.query(OutreachDraft).filter(
            OutreachDraft.id == draft_id,
            OutreachDraft.organization_id == user.organization_id
        ).first()
        if draft:
            draft.is_sent = True
            draft.is_approved = True

    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        action="OUTREACH_LINKEDIN_SENT",
        entity_type="lead",
        entity_id=lead.id,
        details_json=json.dumps({
            "action_type": action_type,
            "profile_url": profile_url,
            "char_count": len(message_body)
        })
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "mode": "linkedin_prepared",
        "action_type": action_type,
        "profile_url": profile_url,
        "char_count": len(message_body),
        "message": f"LinkedIn action recorded in CRM. Follow-up task scheduled for {contact_name}."
    }

import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, ProviderIntegration
from app.api.deps import get_current_user, get_current_active_admin

router = APIRouter(prefix="/settings", tags=["Settings & Integrations"])


class IntegrationConfigRequest(BaseModel):
    provider_type: str  # google_places, search_api, pagespeed, openai, smtp, whatsapp
    is_active: bool
    config: Dict[str, Any]


class IntegrationConfigResponse(BaseModel):
    provider_type: str
    is_active: bool
    masked_config: Dict[str, Any]


def mask_secret(val: Optional[str]) -> str:
    if not val:
        return ""
    if len(val) <= 6:
        return "***"
    return val[:3] + "..." + val[-3:]


@router.get("/integrations", response_model=List[IntegrationConfigResponse])
def get_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    supported = ["google_places", "search_api", "pagespeed", "openai", "smtp", "whatsapp"]
    integrations = db.query(ProviderIntegration).filter(
        ProviderIntegration.organization_id == current_user.organization_id
    ).all()
    int_map = {i.provider_type: i for i in integrations}

    results = []
    for p in supported:
        if p in int_map:
            rec = int_map[p]
            raw_cfg = json.loads(rec.config_json) if rec.config_json else {}
            masked = {}
            for k, v in raw_cfg.items():
                if "key" in k.lower() or "secret" in k.lower() or "password" in k.lower() or "token" in k.lower():
                    masked[k] = mask_secret(str(v))
                else:
                    masked[k] = v
            results.append(IntegrationConfigResponse(
                provider_type=p,
                is_active=rec.is_active,
                masked_config=masked
            ))
        else:
            # Check if environment variable default exists
            env_active = False
            env_masked = {}
            if p == "google_places" and settings.GOOGLE_PLACES_API_KEY:
                env_active = True
                env_masked["api_key"] = mask_secret(settings.GOOGLE_PLACES_API_KEY)
            elif p == "search_api" and settings.SEARCH_API_KEY:
                env_active = True
                env_masked["api_key"] = mask_secret(settings.SEARCH_API_KEY)
            elif p == "openai" and settings.OPENAI_API_KEY:
                env_active = True
                env_masked["api_key"] = mask_secret(settings.OPENAI_API_KEY)

            results.append(IntegrationConfigResponse(
                provider_type=p,
                is_active=env_active,
                masked_config=env_masked
            ))

    return results


@router.post("/integrations", response_model=IntegrationConfigResponse)
def save_integration(
    req: IntegrationConfigRequest,
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    rec = db.query(ProviderIntegration).filter(
        ProviderIntegration.organization_id == current_user.organization_id,
        ProviderIntegration.provider_type == req.provider_type
    ).first()

    if not rec:
        rec = ProviderIntegration(
            organization_id=current_user.organization_id,
            provider_type=req.provider_type,
            is_active=req.is_active,
            config_json=json.dumps(req.config)
        )
        db.add(rec)
    else:
        rec.is_active = req.is_active
        # Merge existing secrets if masked string was sent back unchanged
        existing_cfg = json.loads(rec.config_json) if rec.config_json else {}
        for k, v in req.config.items():
            if v is None or v == "" or str(v).endswith("...") or "..." in str(v):
                # Retain existing secret
                continue
            existing_cfg[k] = v
        rec.config_json = json.dumps(existing_cfg)

    db.commit()
    db.refresh(rec)

    raw_cfg = json.loads(rec.config_json) if rec.config_json else {}
    masked = {}
    for k, v in raw_cfg.items():
        if "key" in k.lower() or "secret" in k.lower() or "password" in k.lower() or "token" in k.lower():
            masked[k] = mask_secret(str(v))
        else:
            masked[k] = v

    return IntegrationConfigResponse(
        provider_type=rec.provider_type,
        is_active=rec.is_active,
        masked_config=masked
    )


class TestEmailRequest(BaseModel):
    host: Optional[str] = None
    port: int = 587
    user: Optional[str] = None
    password: Optional[str] = None
    from_email: Optional[str] = None
    test_recipient: str
    resend_api_key: Optional[str] = None


@router.post("/test-email")
async def test_smtp_connection(
    req: TestEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import smtplib
    import ssl
    import httpx
    from email.mime.text import MIMEText

    # Determine Resend API Key: from request, or resolve from saved DB config if masked/empty
    resend_key = req.resend_api_key.strip() if req.resend_api_key else None
    if not resend_key or "..." in resend_key:
        smtp_rec = db.query(ProviderIntegration).filter(
            ProviderIntegration.organization_id == current_user.organization_id,
            ProviderIntegration.provider_type == "smtp"
        ).first()
        if smtp_rec and smtp_rec.config_json:
            try:
                saved_cfg = json.loads(smtp_rec.config_json)
                saved_key = saved_cfg.get("resend_api_key")
                if saved_key and "..." not in str(saved_key):
                    resend_key = str(saved_key).strip()
            except Exception:
                pass

    # Test HTTP-based Resend API (Port 443 - never blocked on Render)
    if resend_key:
        if not resend_key.startswith("re_"):
            raise HTTPException(
                status_code=400,
                detail="Invalid Resend API Key format. A valid Resend key must start with 're_' (e.g. re_abc123...). Please copy your API key from https://resend.com/api-keys."
            )

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                from_addr = req.from_email if (req.from_email and "@" in req.from_email and not req.from_email.endswith("@gmail.com")) else "onboarding@resend.dev"
                res = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {resend_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": from_addr,
                        "to": [req.test_recipient],
                        "subject": "LeadGen Lite: Resend API Test",
                        "text": "This is a verified test email sent via Resend HTTP API over Port 443."
                    }
                )
                if res.status_code in (200, 201):
                    return {"success": True, "message": f"Test email sent successfully via Resend API to {req.test_recipient}!"}
                elif res.status_code == 401:
                    raise HTTPException(
                        status_code=400,
                        detail="Resend API Key is invalid or expired (401 Unauthorized). Please generate or copy the full API key starting with 're_' from https://resend.com/api-keys and save it."
                    )
                elif res.status_code == 403:
                    try:
                        err_msg = res.json().get("message", res.text)
                    except Exception:
                        err_msg = res.text
                    raise HTTPException(
                        status_code=400,
                        detail=f"Resend Free Tier rule: {err_msg}. Note: On Resend free tier with onboarding@resend.dev, you can only send test emails to your registered Resend account email address."
                    )
                else:
                    try:
                        err_msg = res.json().get("message", res.text)
                    except Exception:
                        err_msg = res.text
                    raise HTTPException(status_code=400, detail=f"Resend API error ({res.status_code}): {err_msg}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to connect to Resend API: {str(e)}")

    # Fallback to SMTP: resolve password from DB if masked or empty
    smtp_host = req.host
    smtp_user = req.user
    smtp_pass = req.password

    if not smtp_pass or "..." in smtp_pass or not smtp_host or not smtp_user:
        smtp_rec = db.query(ProviderIntegration).filter(
            ProviderIntegration.organization_id == current_user.organization_id,
            ProviderIntegration.provider_type == "smtp"
        ).first()
        if smtp_rec and smtp_rec.config_json:
            try:
                saved_cfg = json.loads(smtp_rec.config_json)
                smtp_host = smtp_host or saved_cfg.get("host")
                smtp_user = smtp_user or saved_cfg.get("user")
                if not smtp_pass or "..." in smtp_pass:
                    smtp_pass = saved_cfg.get("password")
            except Exception:
                pass

    if not smtp_host or not smtp_user or not smtp_pass:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid Resend API Key (starts with re_), or enter SMTP Host, User, and Password."
        )

    # Test traditional SMTP socket
    try:
        msg = MIMEText("This is a verified test email from LeadGen Lite Outreach Engine.", "plain", "utf-8")
        msg["Subject"] = "LeadGen Lite: SMTP Configuration Test"
        msg["From"] = req.from_email or smtp_user
        msg["To"] = req.test_recipient

        if req.port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, req.port, context=context, timeout=8.0) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, req.port, timeout=8.0) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

        return {"success": True, "message": f"Test email sent successfully to {req.test_recipient}!"}
    except Exception as e:
        err_str = str(e)
        if "101" in err_str or "unreachable" in err_str.lower():
            err_msg = (
                "Render Free Tier blocks outbound SMTP ports (587, 465, 25). "
                "To send emails: (1) Use the 1-Click 'Mail App' button in Lead Drawer to send directly via Gmail from your device, "
                "or (2) enter a free Resend API Key above which sends over HTTPS (Port 443)."
            )
        else:
            err_msg = err_str
        raise HTTPException(status_code=400, detail=f"SMTP handshake failed: {err_msg}")

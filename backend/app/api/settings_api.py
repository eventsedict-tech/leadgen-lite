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
            if str(v).endswith("...") or "..." in str(v):
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
    current_user: User = Depends(get_current_user)
):
    import smtplib
    import ssl
    import httpx
    from email.mime.text import MIMEText

    # Test HTTP-based Resend API (Port 443 - never blocked on Render)
    if req.resend_api_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                from_addr = req.from_email if (req.from_email and "@" in req.from_email and not req.from_email.endswith("@gmail.com")) else "onboarding@resend.dev"
                res = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {req.resend_api_key}",
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
                else:
                    raise HTTPException(status_code=400, detail=f"Resend API error: {res.text}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to connect to Resend API: {str(e)}")

    if not req.host or not req.user or not req.password:
        raise HTTPException(status_code=400, detail="Please enter SMTP Host, User, and Password, or enter a Resend API Key.")

    # Test traditional SMTP socket
    try:
        msg = MIMEText("This is a verified test email from LeadGen Lite Outreach Engine.", "plain", "utf-8")
        msg["Subject"] = "LeadGen Lite: SMTP Configuration Test"
        msg["From"] = req.from_email or req.user
        msg["To"] = req.test_recipient

        if req.port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(req.host, req.port, context=context, timeout=8.0) as server:
                server.login(req.user, req.password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(req.host, req.port, timeout=8.0) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(req.user, req.password)
                server.send_message(msg)

        return {"success": True, "message": f"Test email sent successfully to {req.test_recipient}!"}
    except Exception as e:
        err_str = str(e)
        if "101" in err_str or "unreachable" in err_str.lower():
            err_msg = (
                "Render Free Tier blocks outbound SMTP ports (587, 465, 25). "
                "To send emails: (1) Use the 1-Click 'Mail App' button in Lead Drawer to send directly via Gmail from your device, "
                "or (2) enter a free Resend API Key below which sends over HTTPS (Port 443)."
            )
        else:
            err_msg = err_str
        raise HTTPException(status_code=400, detail=f"SMTP handshake failed: {err_msg}")

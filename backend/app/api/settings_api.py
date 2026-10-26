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

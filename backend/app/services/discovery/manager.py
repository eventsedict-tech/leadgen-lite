import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import ProviderIntegration
from app.services.discovery.base import (
    BaseDiscoveryProvider, DiscoveredCompany, DiscoveryQuery, ProviderInfo
)
from app.services.discovery.google_places import GooglePlacesProvider
from app.services.discovery.search_api import SearchApiProvider
from app.services.discovery.test_mock import TestMockProvider


class DiscoveryManager:
    def __init__(self):
        self.providers: Dict[str, BaseDiscoveryProvider] = {
            "google_places": GooglePlacesProvider(),
            "search_api": SearchApiProvider(),
            "test_mock": TestMockProvider()
        }

    def _get_org_provider_key(self, db: Session, org_id: int, provider_id: str) -> Optional[str]:
        integration = db.query(ProviderIntegration).filter(
            ProviderIntegration.organization_id == org_id,
            ProviderIntegration.provider_type == provider_id,
            ProviderIntegration.is_active == True
        ).first()
        if integration and integration.config_json:
            try:
                cfg = json.loads(integration.config_json)
                return cfg.get("api_key")
            except Exception:
                pass
        return None

    def list_providers(self, db: Session, org_id: int) -> List[ProviderInfo]:
        info_list = []
        for pid, provider in self.providers.items():
            key = self._get_org_provider_key(db, org_id, pid)
            info_list.append(provider.get_info(custom_key=key))
        return info_list

    async def search(
        self,
        provider_id: str,
        query: DiscoveryQuery,
        db: Session,
        org_id: int
    ) -> List[DiscoveredCompany]:
        if provider_id not in self.providers:
            raise ValueError(f"Unknown discovery provider '{provider_id}'")

        provider = self.providers[provider_id]
        key = self._get_org_provider_key(db, org_id, provider_id)

        if not provider.is_configured(custom_key=key):
            info = provider.get_info(custom_key=key)
            raise ValueError(
                f"Provider '{info.name}' is not configured with an API key. "
                f"Instructions: {info.setup_instructions}"
            )

        return await provider.discover(query, custom_key=key)


discovery_manager = DiscoveryManager()

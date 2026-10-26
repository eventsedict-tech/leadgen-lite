import httpx
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.services.discovery.base import BaseDiscoveryProvider, DiscoveredCompany, DiscoveryQuery, ProviderInfo


class SearchApiProvider(BaseDiscoveryProvider):
    provider_id = "search_api"
    display_name = "Authorized Search API (SerpApi / ValueSERP)"

    def __init__(self):
        self.default_api_key = settings.SEARCH_API_KEY

    def is_configured(self, custom_key: Optional[str] = None) -> bool:
        key = custom_key or self.default_api_key
        return bool(key and key.strip())

    def get_info(self, custom_key: Optional[str] = None) -> ProviderInfo:
        return ProviderInfo(
            id=self.provider_id,
            name=self.display_name,
            is_configured=self.is_configured(custom_key),
            description="Query structured local business listings and websites through authorized commercial search APIs.",
            setup_instructions="Sign up for SerpApi or ValueSERP and set SEARCH_API_KEY in your environment or Settings.",
            docs_url="https://serpapi.com/google-local-api"
        )

    async def discover(self, query: DiscoveryQuery, custom_key: Optional[str] = None) -> List[DiscoveredCompany]:
        api_key = custom_key or self.default_api_key
        if not api_key:
            raise ValueError("Search API is not configured. Please supply an authorized API key in Settings.")

        query_str = f"{query.industry or ''} {query.keywords or ''} in {query.city or ''} {query.state or ''} {query.country or ''}".strip()
        endpoint = "https://serpapi.com/search.json"
        params = {
            "engine": "google_local",
            "q": query_str or "businesses",
            "api_key": api_key,
            "num": query.limit
        }

        discovered: List[DiscoveredCompany] = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(endpoint, params=params)
            if resp.status_code != 200:
                raise RuntimeError(f"Search API request failed with HTTP {resp.status_code}")

            data = resp.json()
            local_results = data.get("local_results", [])[:query.limit]

            for item in local_results:
                title = item.get("title")
                website = item.get("website")
                phone = item.get("phone")
                address = item.get("address")
                rating = item.get("rating")
                reviews = item.get("reviews")

                if query.require_website and not website:
                    continue
                if query.require_contact and not phone:
                    continue

                discovered.append(DiscoveredCompany(
                    company_name=title,
                    official_website=website,
                    industry=query.industry,
                    city=query.city,
                    state=query.state,
                    country=query.country,
                    public_business_phone=phone,
                    public_business_address=address,
                    source_url=item.get("link"),
                    data_source="Search API (SerpApi)",
                    rating=rating,
                    user_ratings_total=reviews,
                    raw_details=item
                ))

        return discovered

import httpx
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.services.discovery.base import BaseDiscoveryProvider, DiscoveredCompany, DiscoveryQuery, ProviderInfo


class GooglePlacesProvider(BaseDiscoveryProvider):
    provider_id = "google_places"
    display_name = "Google Places API"

    def __init__(self):
        self.default_api_key = settings.GOOGLE_PLACES_API_KEY

    def is_configured(self, custom_key: Optional[str] = None) -> bool:
        key = custom_key or self.default_api_key
        return bool(key and key.strip())

    def get_info(self, custom_key: Optional[str] = None) -> ProviderInfo:
        return ProviderInfo(
            id=self.provider_id,
            name=self.display_name,
            is_configured=self.is_configured(custom_key),
            description="Discover verified local business listings, addresses, phone numbers, and websites worldwide using Google's official Places API.",
            setup_instructions="Obtain an API key from Google Cloud Console with Places API (New) enabled. Set GOOGLE_PLACES_API_KEY in your environment or Settings.",
            docs_url="https://developers.google.com/maps/documentation/places/web-service/overview"
        )

    async def discover(self, query: DiscoveryQuery, custom_key: Optional[str] = None) -> List[DiscoveredCompany]:
        api_key = custom_key or self.default_api_key
        if not api_key:
            raise ValueError("Google Places API is not configured. Please supply an authorized API key in Settings.")

        query_parts = []
        if query.industry:
            query_parts.append(query.industry)
        if query.keywords:
            query_parts.append(query.keywords)
        if query.city:
            query_parts.append(query.city)
        if query.state:
            query_parts.append(query.state)
        if query.country:
            query_parts.append(query.country)

        search_text = " ".join(query_parts) if query_parts else "business"

        endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": search_text,
            "key": api_key
        }

        discovered: List[DiscoveredCompany] = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(endpoint, params=params)
            if resp.status_code != 200:
                raise RuntimeError(f"Google Places API request failed with HTTP {resp.status_code}: {resp.text}")

            data = resp.json()
            status_code = data.get("status")
            if status_code not in ("OK", "ZERO_RESULTS"):
                err_msg = data.get("error_message") or status_code
                raise RuntimeError(f"Google Places API error: {err_msg}")

            results = data.get("results", [])[:query.limit]

            for place in results:
                place_id = place.get("place_id")
                name = place.get("name")
                formatted_address = place.get("formatted_address")
                rating = place.get("rating")
                user_ratings_total = place.get("user_ratings_total")

                # Fetch details for website & phone if available
                website = None
                phone = None
                if place_id:
                    try:
                        detail_resp = await client.get(
                            "https://maps.googleapis.com/maps/api/place/details/json",
                            params={
                                "place_id": place_id,
                                "fields": "website,formatted_phone_number,url",
                                "key": api_key
                            }
                        )
                        if detail_resp.status_code == 200:
                            detail_data = detail_resp.json().get("result", {})
                            website = detail_data.get("website")
                            phone = detail_data.get("formatted_phone_number")
                    except Exception:
                        pass

                if query.require_website and not website:
                    continue
                if query.require_contact and not phone:
                    continue

                discovered.append(DiscoveredCompany(
                    company_name=name,
                    official_website=website,
                    industry=query.industry,
                    city=query.city,
                    state=query.state,
                    country=query.country,
                    public_business_phone=phone,
                    public_business_address=formatted_address,
                    source_url=f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else None,
                    data_source="Google Places API",
                    rating=rating,
                    user_ratings_total=user_ratings_total,
                    raw_details=place
                ))

        return discovered

from typing import Optional, List
from app.services.discovery.base import BaseDiscoveryProvider, DiscoveredCompany, DiscoveryQuery, ProviderInfo


class TestMockProvider(BaseDiscoveryProvider):
    provider_id = "test_mock"
    display_name = "Test & Evaluation Business Directory (Offline)"

    def is_configured(self, custom_key: Optional[str] = None) -> bool:
        return True

    def get_info(self, custom_key: Optional[str] = None) -> ProviderInfo:
        return ProviderInfo(
            id=self.provider_id,
            name=self.display_name,
            is_configured=True,
            description="Built-in offline test provider for evaluating search filtering, lead scoring, and pipeline ingestion without external API keys.",
            setup_instructions="Ready to use immediately without credentials.",
            docs_url="https://leadgenlite.local/docs/providers"
        )

    async def discover(self, query: DiscoveryQuery, custom_key: Optional[str] = None) -> List[DiscoveredCompany]:
        city = query.city or "Austin"
        industry = query.industry or "Digital Marketing"

        sample_database = [
            DiscoveredCompany(
                company_name=f"{city} Peak Real Estate Co",
                official_website="https://peakrealestate-demo.com",
                industry="Real Estate",
                city=city,
                state=query.state or "TX",
                country=query.country or "USA",
                public_business_phone="+1-512-555-0144",
                public_business_address=f"101 Congress Ave, {city}",
                source_url="https://testdirectory.local/listing/101",
                data_source="Test & Evaluation Directory",
                rating=4.2,
                user_ratings_total=38
            ),
            DiscoveredCompany(
                company_name=f"{city} Horizon Dental Care",
                official_website="https://horizondental-demo.com",
                industry="Healthcare",
                city=city,
                state=query.state or "TX",
                country=query.country or "USA",
                public_business_phone="+1-512-555-0188",
                public_business_address=f"450 Guadalupe St, {city}",
                source_url="https://testdirectory.local/listing/102",
                data_source="Test & Evaluation Directory",
                rating=4.7,
                user_ratings_total=95
            ),
            DiscoveredCompany(
                company_name=f"Vanguard Legal Partners {city}",
                official_website=None,  # Intentionally missing website for marketing opportunity detection
                industry="Legal",
                city=city,
                state=query.state or "TX",
                country=query.country or "USA",
                public_business_phone="+1-512-555-0199",
                public_business_address=f"789 Lavaca St, {city}",
                source_url="https://testdirectory.local/listing/103",
                data_source="Test & Evaluation Directory",
                rating=3.9,
                user_ratings_total=14
            ),
            DiscoveredCompany(
                company_name=f"{city} EcoRoofing & Solar",
                official_website="http://ecoroofingsolar-demo.org",  # Insecure HTTP
                industry="Construction",
                city=city,
                state=query.state or "TX",
                country=query.country or "USA",
                public_business_phone="+1-512-555-0122",
                public_business_address=f"200 Lamar Blvd, {city}",
                source_url="https://testdirectory.local/listing/104",
                data_source="Test & Evaluation Directory",
                rating=4.5,
                user_ratings_total=52
            )
        ]

        filtered = []
        for c in sample_database:
            if query.require_website and not c.official_website:
                continue
            if query.require_contact and not c.public_business_phone:
                continue
            filtered.append(c)

        return filtered[:query.limit]

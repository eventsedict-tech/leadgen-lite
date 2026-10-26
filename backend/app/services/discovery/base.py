from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DiscoveredCompany(BaseModel):
    company_name: str
    official_website: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    public_business_phone: Optional[str] = None
    public_business_address: Optional[str] = None
    source_url: Optional[str] = None
    data_source: str
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    raw_details: Optional[Dict[str, Any]] = None


class DiscoveryQuery(BaseModel):
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    keywords: Optional[str] = None
    require_website: bool = False
    require_contact: bool = False
    limit: int = Field(default=20, ge=1, le=60)


class ProviderInfo(BaseModel):
    id: str
    name: str
    is_configured: bool
    description: str
    setup_instructions: str
    docs_url: str


class BaseDiscoveryProvider(ABC):
    provider_id: str
    display_name: str

    @abstractmethod
    def is_configured(self, custom_key: Optional[str] = None) -> bool:
        """Returns True if the provider has valid API credentials configured."""
        pass

    @abstractmethod
    def get_info(self, custom_key: Optional[str] = None) -> ProviderInfo:
        """Returns metadata and setup instructions for this provider."""
        pass

    @abstractmethod
    async def discover(self, query: DiscoveryQuery, custom_key: Optional[str] = None) -> List[DiscoveredCompany]:
        """Discovers companies matching the search criteria."""
        pass

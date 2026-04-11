from pathlib import Path
import yaml

from app.data.models import DomainType

PROFILES_DIR = Path(__file__).resolve().parents[3] / "domain_profiles"


class DomainConfig:
    """Loads and provides domain-specific configuration."""

    def __init__(self, domain: DomainType):
        self.domain = domain
        self._config = self._load_profile(domain)

    def _load_profile(self, domain: DomainType) -> dict:
        path = PROFILES_DIR / f"{domain.value}.yaml"
        if not path.exists():
            return {"domain": domain.value}
        with open(path) as f:
            return yaml.safe_load(f)

    @property
    def display_name(self) -> str:
        return self._config.get("display_name", self.domain.value)

    @property
    def entity_mappings(self) -> dict:
        return self._config.get("entity_mappings", {})

    @property
    def talent_label(self) -> str:
        return self.entity_mappings.get("talent", "Speaker")

    @property
    def funder_label(self) -> str:
        return self.entity_mappings.get("funder", "Sponsor")

    @property
    def sponsor_tiers(self) -> list[dict]:
        return self._config.get("sponsor_tiers", [])

    @property
    def ticket_types(self) -> list[str]:
        return self._config.get("ticket_types", [])

    @property
    def scoring_weights(self) -> dict:
        return self._config.get("scoring_weights", {})

    @property
    def scraping_sources(self) -> dict:
        return self._config.get("scraping_sources", {})

    @property
    def community_channels(self) -> dict:
        return self._config.get("community_channels", {})

    def get(self, key: str, default=None):
        return self._config.get(key, default)

"""Scraper for confs.tech — fetches open-source GitHub JSON data directly (no scraping needed)."""
import logging
import httpx

from ..base import BaseScraper
from ..normalize import make_event

logger = logging.getLogger(__name__)

BASE = "https://raw.githubusercontent.com/tech-conferences/conference-data/main/conferences"

TOPICS_2025 = [
    "accessibility", "android", "api", "cfml", "cpp", "css", "data", "devops",
    "dotnet", "general", "identity", "ios", "iot", "java", "javascript", "kotlin",
    "leadership", "networking", "opensource", "performance", "php", "product",
    "python", "ruby", "rust", "scala", "security", "sre", "testing", "typescript", "ux",
]

TOPICS_2026 = [
    "accessibility", "android", "api", "css", "data", "devops", "dotnet", "general",
    "graphql", "ios", "iot", "java", "javascript", "kotlin", "leadership", "networking",
    "opensource", "performance", "php", "product", "python", "rust", "security", "sre",
    "testing", "typescript", "ux",
]


class ConfTechScraper(BaseScraper):
    source_name = "conf.tech"

    async def scrape(self, **kwargs) -> list[dict]:
        """Fetch all topic JSON files from the GitHub repo via httpx."""
        raw_events = []
        urls = (
            [(f"{BASE}/2025/{t}.json", t, 2025) for t in TOPICS_2025]
            + [(f"{BASE}/2026/{t}.json", t, 2026) for t in TOPICS_2026]
        )

        async with httpx.AsyncClient(timeout=15) as client:
            for url, topic, year in urls:
                try:
                    r = await client.get(url)
                    if r.status_code == 200:
                        events = r.json()
                        for e in events:
                            e["_topic"] = topic
                            e["_year"] = year
                        raw_events.extend(events)
                    else:
                        logger.warning(f"[{self.source_name}] {url} → HTTP {r.status_code}")
                except Exception as exc:
                    logger.warning(f"[{self.source_name}] Failed {url}: {exc}")

        logger.info(f"[{self.source_name}] Fetched {len(raw_events)} raw records from GitHub")
        return raw_events

    def normalize(self, raw: dict) -> dict | None:
        name = (raw.get("name") or "").strip()
        if not name:
            return None

        return make_event(
            name=name,
            domain="conference",
            category=raw.get("_topic", "Technology").replace("-", "/").title(),
            start_date=raw.get("startDate"),
            end_date=raw.get("endDate"),
            city=raw.get("city"),
            country=raw.get("country"),
            website_url=raw.get("url"),
            data_source="confs.tech (github)",
            extraction_method="github_json",
            raw_data={k: v for k, v in raw.items() if not k.startswith("_")},
        )

"""Scraper for conf.tech — tech conference aggregator."""
import json
import logging

from crawl4ai import CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from ..base import BaseScraper
from ..normalize import make_event

logger = logging.getLogger(__name__)

# CSS schema for conf.tech event cards
SCHEMA = {
    "name": "conferences",
    "baseSelector": "li.conference",
    "fields": [
        {"name": "title", "selector": "a", "type": "text"},
        {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
        {"name": "date", "selector": ".conference-date", "type": "text"},
        {"name": "location", "selector": ".conference-location", "type": "text"},
        {"name": "tags", "selector": ".conference-tag", "type": "text"},
    ],
}

YEARS = [2025, 2026]
BASE_URL = "https://confs.tech"


def _parse_location(raw: str | None) -> tuple[str | None, str | None]:
    if not raw:
        return None, None
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    return raw.strip(), None


class ConfTechScraper(BaseScraper):
    source_name = "conf.tech"

    async def scrape(self, topics: list[str] | None = None) -> list[dict]:
        topics = topics or ["javascript", "ux", "devops", "general", "security", "data", "ai-ml"]
        raw_events: list[dict] = []

        config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(schema=SCHEMA),
            cache_mode=CacheMode.ENABLED,
            remove_overlay_elements=True,
            page_timeout=30000,
        )

        for year in YEARS:
            urls = [f"{BASE_URL}/?year={year}&topic={t}" for t in topics]
            results = await self.crawl_many(urls, config)

            for result in results:
                if not result.success or not result.extracted_content:
                    continue
                try:
                    data = json.loads(result.extracted_content)
                    raw_events.extend(data if isinstance(data, list) else [])
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"[{self.source_name}] Could not parse JSON from {result.url}")

        return raw_events

    def normalize(self, raw: dict) -> dict | None:
        name = raw.get("title", "").strip()
        if not name:
            return None

        city, country = _parse_location(raw.get("location"))
        url = raw.get("url", "")
        if url and not url.startswith("http"):
            url = f"https://confs.tech{url}"

        return make_event(
            name=name,
            domain="conference",
            category=raw.get("tags", "Technology"),
            start_date=raw.get("date"),
            city=city,
            country=country,
            website_url=url,
            data_source="confs.tech",
            extraction_method="crawl4ai_css",
            raw_data=raw,
        )

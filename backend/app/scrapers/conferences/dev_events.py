"""Scraper for dev.events — developer conference aggregator."""
import json
import logging

from crawl4ai import CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from ..base import BaseScraper
from ..normalize import make_event

logger = logging.getLogger(__name__)

SCHEMA = {
    "name": "events",
    "baseSelector": ".event-item, .event, article",
    "fields": [
        {"name": "title", "selector": "h2, h3, .title", "type": "text"},
        {"name": "date", "selector": ".date, time, .event-date", "type": "text"},
        {"name": "city", "selector": ".city, .location", "type": "text"},
        {"name": "country", "selector": ".country", "type": "text"},
        {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
        {"name": "tags", "selector": ".tag, .category", "type": "text"},
        {"name": "cfp_deadline", "selector": ".cfp, .cfp-date", "type": "text"},
    ],
}

PAGES = [
    "https://dev.events/?year=2025",
    "https://dev.events/?year=2026",
    "https://dev.events/categories/ai?year=2025",
    "https://dev.events/categories/ai?year=2026",
]


class DevEventsScraper(BaseScraper):
    source_name = "dev.events"

    async def scrape(self, **kwargs) -> list[dict]:
        config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(schema=SCHEMA),
            cache_mode=CacheMode.ENABLED,
            remove_overlay_elements=True,
            excluded_tags=["nav", "footer"],
            page_timeout=30000,
        )

        results = await self.crawl_many(PAGES, config)
        raw_events: list[dict] = []

        for result in results:
            if not result.success or not result.extracted_content:
                continue
            try:
                data = json.loads(result.extracted_content)
                raw_events.extend(data if isinstance(data, list) else [])
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"[{self.source_name}] Parse error: {result.url}")

        return raw_events

    def normalize(self, raw: dict) -> dict | None:
        name = raw.get("title", "").strip()
        if not name:
            return None

        url = raw.get("url", "")
        if url and not url.startswith("http"):
            url = f"https://dev.events{url}"

        return make_event(
            name=name,
            domain="conference",
            category=raw.get("tags", "Developer"),
            start_date=raw.get("date"),
            city=raw.get("city"),
            country=raw.get("country"),
            website_url=url,
            data_source="dev.events",
            extraction_method="crawl4ai_css",
            raw_data=raw,
        )

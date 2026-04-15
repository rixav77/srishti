"""Scraper for JamBase — festival and concert guide."""
import json
import logging

from crawl4ai import CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from ..base import BaseScraper
from ..normalize import make_event

logger = logging.getLogger(__name__)

SCHEMA = {
    "name": "festivals",
    "baseSelector": ".event-listing, .festival-card, article",
    "fields": [
        {"name": "title", "selector": "h2, h3, .event-name, .festival-name", "type": "text"},
        {"name": "date", "selector": "time, .date, .event-date", "type": "text"},
        {"name": "venue", "selector": ".venue, .venue-name", "type": "text"},
        {"name": "city", "selector": ".city, .location", "type": "text"},
        {"name": "country", "selector": ".country, .state", "type": "text"},
        {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
        {"name": "genre", "selector": ".genre, .tag", "type": "text"},
    ],
}

PAGES = [
    "https://www.jambase.com/festivals/2025",
    "https://www.jambase.com/festivals/2026",
    "https://www.jambase.com/festivals/2025?page=2",
]


class JamBaseScraper(BaseScraper):
    source_name = "jambase"

    async def scrape(self, **kwargs) -> list[dict]:
        config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(schema=SCHEMA),
            cache_mode=CacheMode.ENABLED,
            remove_overlay_elements=True,
            excluded_tags=["nav", "footer", "aside"],
            page_timeout=40000,
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
            url = f"https://www.jambase.com{url}"

        return make_event(
            name=name,
            domain="music_festival",
            category=raw.get("genre", "Music"),
            start_date=raw.get("date"),
            city=raw.get("city"),
            country=raw.get("country") or "USA",
            venue_name=raw.get("venue"),
            website_url=url,
            data_source="jambase.com",
            extraction_method="crawl4ai_css",
            raw_data=raw,
        )

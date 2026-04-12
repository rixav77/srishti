"""Scraper for lu.ma — JS-rendered tech event platform."""
import json
import logging

from crawl4ai import CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from ..base import BaseScraper
from ..normalize import make_event

logger = logging.getLogger(__name__)

SCHEMA = {
    "name": "events",
    "baseSelector": "[data-testid='event-card'], .event-card, article",
    "fields": [
        {"name": "title", "selector": "h2, h3, .event-title", "type": "text"},
        {"name": "date", "selector": "time, .event-date", "type": "text"},
        {"name": "location", "selector": ".event-location, .location", "type": "text"},
        {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
        {"name": "hosts", "selector": ".host-name, .organizer", "type": "text"},
    ],
}

PAGES = [
    "https://lu.ma/discover?category=tech&start=2025-01-01",
    "https://lu.ma/discover?category=tech&start=2026-01-01",
    "https://lu.ma/discover?category=ai&start=2025-01-01",
    "https://lu.ma/discover?category=ai&start=2026-01-01",
]


def _parse_luma_location(raw: str | None) -> tuple[str | None, str | None]:
    if not raw:
        return None, None
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    return raw.strip(), None


class LumaScraper(BaseScraper):
    source_name = "luma"
    max_concurrent = 2  # Luma is stricter with rate limits

    async def scrape(self, **kwargs) -> list[dict]:
        config = CrawlerRunConfig(
            # Wait for JS-rendered event cards
            wait_for="css:[data-testid='event-card'], css:.event-card",
            js_code="window.scrollTo(0, document.body.scrollHeight);",
            extraction_strategy=JsonCssExtractionStrategy(schema=SCHEMA),
            cache_mode=CacheMode.ENABLED,
            remove_overlay_elements=True,
            page_timeout=60000,
        )

        results = await self.crawl_many(PAGES, config)
        raw_events: list[dict] = []

        for result in results:
            if not result.success or not result.extracted_content:
                logger.warning(f"[{self.source_name}] No content: {result.url}")
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

        city, country = _parse_luma_location(raw.get("location"))
        url = raw.get("url", "")
        if url and not url.startswith("http"):
            url = f"https://lu.ma{url}"

        return make_event(
            name=name,
            domain="conference",
            category="Technology",
            start_date=raw.get("date"),
            city=city,
            country=country,
            website_url=url,
            data_source="lu.ma",
            extraction_method="crawl4ai_css_js",
            raw_data=raw,
        )

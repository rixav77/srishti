"""Scraper for 10times.com — global events directory."""
import json
import logging

from crawl4ai import CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from ..base import BaseScraper
from ..normalize import make_event

logger = logging.getLogger(__name__)

SCHEMA = {
    "name": "events",
    "baseSelector": ".event-listing, .event-card, article.event",
    "fields": [
        {"name": "title", "selector": "h2, h3, .event-name", "type": "text"},
        {"name": "date", "selector": ".event-date, .date, time", "type": "text"},
        {"name": "city", "selector": ".event-city, .city", "type": "text"},
        {"name": "country", "selector": ".event-country, .country", "type": "text"},
        {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
        {"name": "category", "selector": ".category, .tag", "type": "text"},
        {"name": "attendance", "selector": ".visitors, .attendance", "type": "text"},
    ],
}

PAGES = [
    "https://10times.com/technology?month=2025",
    "https://10times.com/technology?month=2026",
    "https://10times.com/ai-ml?month=2025",
    "https://10times.com/ai-ml?month=2026",
    "https://10times.com/business?month=2025",
    "https://10times.com/business?month=2026",
]


def _parse_attendance(raw: str | None) -> int | None:
    if not raw:
        return None
    import re
    m = re.search(r"([\d,]+)", raw.replace(",", ""))
    return int(m.group(1)) if m else None


class TenTimesScraper(BaseScraper):
    source_name = "10times"

    async def scrape(self, **kwargs) -> list[dict]:
        config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(schema=SCHEMA),
            cache_mode=CacheMode.ENABLED,
            remove_overlay_elements=True,
            excluded_tags=["nav", "footer", "aside", "script"],
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
            url = f"https://10times.com{url}"

        return make_event(
            name=name,
            domain="conference",
            category=raw.get("category", "Technology"),
            start_date=raw.get("date"),
            city=raw.get("city"),
            country=raw.get("country"),
            estimated_attendance=_parse_attendance(raw.get("attendance")),
            website_url=url,
            data_source="10times.com",
            extraction_method="crawl4ai_css",
            raw_data=raw,
        )

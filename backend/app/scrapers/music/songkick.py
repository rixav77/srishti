"""Scraper for Songkick — music festival listings."""
import json
import logging

from crawl4ai import CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from ..base import BaseScraper
from ..normalize import make_event

logger = logging.getLogger(__name__)

SCHEMA = {
    "name": "festivals",
    "baseSelector": "li.event-listing, article.event, .event-item",
    "fields": [
        {"name": "title", "selector": "strong.summary, h3, .event-name", "type": "text"},
        {"name": "date", "selector": "time, .event-date, .date", "type": "text"},
        {"name": "venue", "selector": ".venue-name, .location-name", "type": "text"},
        {"name": "city", "selector": ".city-name, .city", "type": "text"},
        {"name": "country", "selector": ".country-name, .country", "type": "text"},
        {"name": "url", "selector": "a.event-link, a", "type": "attribute", "attribute": "href"},
        {"name": "artists", "selector": ".artist-name", "type": "text"},
    ],
}

PAGES = [
    "https://www.songkick.com/festivals/2025",
    "https://www.songkick.com/festivals/2026",
    "https://www.songkick.com/festivals/2025?page=2",
    "https://www.songkick.com/festivals/2025?page=3",
]


class SongkickScraper(BaseScraper):
    source_name = "songkick"
    max_concurrent = 2

    async def scrape(self, **kwargs) -> list[dict]:
        config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(schema=SCHEMA),
            cache_mode=CacheMode.ENABLED,
            remove_overlay_elements=True,
            css_selector="main, #event-listings, .events-list",
            excluded_tags=["nav", "footer", "aside"],
            page_timeout=45000,
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

        url = raw.get("url", "")
        if url and not url.startswith("http"):
            url = f"https://www.songkick.com{url}"

        # Artists as speakers equivalent
        artists_raw = raw.get("artists", "")
        artists = [a.strip() for a in artists_raw.split(",") if a.strip()] if artists_raw else []

        return make_event(
            name=name,
            domain="music_festival",
            category="Music",
            start_date=raw.get("date"),
            city=raw.get("city"),
            country=raw.get("country"),
            venue_name=raw.get("venue"),
            speakers=artists,
            website_url=url,
            data_source="songkick.com",
            extraction_method="crawl4ai_css",
            raw_data=raw,
        )

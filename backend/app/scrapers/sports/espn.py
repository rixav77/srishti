"""Scraper for ESPN — sporting events. Uses LLM extraction for irregular layouts."""
import json
import logging
import os

from crawl4ai import CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from ..base import BaseScraper
from ..normalize import make_event

logger = logging.getLogger(__name__)

EXTRACTION_INSTRUCTION = """
Extract all sporting events from this page. For each event return a JSON object with:
- event_name: full name of the event (e.g. "Super Bowl LIX", "ICC Cricket World Cup 2025")
- sport: the sport type (e.g. "Football", "Cricket", "Basketball", "Tennis")
- start_date: start date in YYYY-MM-DD format if known
- end_date: end date in YYYY-MM-DD format if known
- venue: venue or stadium name
- city: host city
- country: host country
- estimated_attendance: number if mentioned
- website_url: official website URL if mentioned

Return a JSON array of these objects. Only include events from 2025 or 2026.
"""

PAGES = [
    "https://www.espn.com/nfl/schedule/_/year/2025",
    "https://www.espn.com/nba/schedule/_/year/2025",
    "https://www.espn.com/soccer/schedule/_/year/2025",
    "https://en.wikipedia.org/wiki/List_of_sports_events_in_2025",
    "https://en.wikipedia.org/wiki/List_of_sports_events_in_2026",
]


class ESPNScraper(BaseScraper):
    source_name = "espn"
    max_concurrent = 2

    def _make_config(self) -> CrawlerRunConfig:
        groq_api_key = os.getenv("GROQ_API_KEY", "")

        bm25_filter = BM25ContentFilter(
            user_query="sporting event 2025 2026 stadium venue attendance",
            bm25_threshold=1.0,
        )

        extraction_strategy = LLMExtractionStrategy(
            provider="groq/llama-3.1-8b-instant",
            api_token=groq_api_key,
            instruction=EXTRACTION_INSTRUCTION,
            extraction_type="json",
            verbose=False,
        )

        return CrawlerRunConfig(
            markdown_generator=DefaultMarkdownGenerator(content_filter=bm25_filter),
            extraction_strategy=extraction_strategy,
            cache_mode=CacheMode.ENABLED,
            remove_overlay_elements=True,
            excluded_tags=["nav", "footer", "aside", "script", "style"],
            page_timeout=60000,
        )

    async def scrape(self, **kwargs) -> list[dict]:
        config = self._make_config()
        results = await self.crawl_many(PAGES, config)
        raw_events: list[dict] = []

        for result in results:
            if not result.success or not result.extracted_content:
                logger.warning(f"[{self.source_name}] No content: {result.url}")
                continue
            try:
                data = json.loads(result.extracted_content)
                if isinstance(data, list):
                    raw_events.extend(data)
                elif isinstance(data, dict) and "events" in data:
                    raw_events.extend(data["events"])
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"[{self.source_name}] Parse error: {result.url}")

        return raw_events

    def normalize(self, raw: dict) -> dict | None:
        name = raw.get("event_name", "").strip()
        if not name:
            return None

        return make_event(
            name=name,
            domain="sporting_event",
            category=raw.get("sport", "Sports"),
            start_date=raw.get("start_date"),
            end_date=raw.get("end_date"),
            city=raw.get("city"),
            country=raw.get("country"),
            venue_name=raw.get("venue"),
            estimated_attendance=raw.get("estimated_attendance"),
            website_url=raw.get("website_url"),
            data_source="espn.com + wikipedia",
            extraction_method="crawl4ai_llm_groq",
            raw_data=raw,
        )

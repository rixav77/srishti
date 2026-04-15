"""Scraper for dev.events — developer conference aggregator."""
import json
import logging

from crawl4ai import CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from ..base import BaseScraper, BROWSER_CONFIG
from ..normalize import make_event

logger = logging.getLogger(__name__)

STEALTH_BROWSER = BrowserConfig(
    headless=True,
    enable_stealth=True,
    user_agent_mode="random",
    viewport_width=1366,
    viewport_height=768,
)

# Verified selector from HTML inspection:
# <div class="row columns is-mobile featured/non-featured">
#   <div class="column is-one-quarter"><time>..date..</time></div>
#   <div class="column"><h2><a href="url">title</a></h2><h3>description</h3></div>
# </div>
SCHEMA = {
    "name": "conferences",
    "baseSelector": "div.row.columns.is-mobile",
    "fields": [
        {"name": "title", "selector": "h2 a", "type": "text"},
        {"name": "url",   "selector": "h2 a", "type": "attribute", "attribute": "href"},
        {"name": "date",  "selector": "time",  "type": "text"},
        {"name": "description", "selector": "h3", "type": "text"},
    ],
}

# Topic + region pages — gives broad coverage
PAGES = [
    "https://dev.events/python?year=2025",
    "https://dev.events/javascript?year=2025",
    "https://dev.events/data?year=2025",
    "https://dev.events/devops?year=2025",
    "https://dev.events/security?year=2025",
    "https://dev.events/ai?year=2025",
    "https://dev.events/python?year=2026",
    "https://dev.events/javascript?year=2026",
    "https://dev.events/data?year=2026",
    "https://dev.events/ai?year=2026",
]


def _guess_year(date_str: str, url: str) -> int | None:
    """dev.events dates are like 'May 28-29' with year in span — guess from page URL."""
    import re
    m = re.search(r"year=(\d{4})", url)
    return int(m.group(1)) if m else None


class DevEventsScraper(BaseScraper):
    source_name = "dev.events"
    max_concurrent = 2

    async def scrape(self, **kwargs) -> list[dict]:
        from crawl4ai import AsyncWebCrawler

        config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(schema=SCHEMA),
            cache_mode=CacheMode.ENABLED,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            remove_overlay_elements=True,
            excluded_tags=["nav", "footer", "aside"],
            page_timeout=40000,
        )

        raw_events: list[dict] = []
        async with AsyncWebCrawler(config=STEALTH_BROWSER) as crawler:
            results = await crawler.arun_many(PAGES, config=config, max_concurrent=self.max_concurrent)

        for result, url in zip(results, PAGES):
            if not result.success or not result.extracted_content:
                logger.warning(f"[{self.source_name}] No content: {url}")
                continue
            try:
                data = json.loads(result.extracted_content)
                year = _guess_year("", url)
                for item in (data if isinstance(data, list) else []):
                    item["_year"] = year
                    item["_source_url"] = url
                raw_events.extend(data if isinstance(data, list) else [])
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"[{self.source_name}] Parse error: {url}")

        return raw_events

    def normalize(self, raw: dict) -> dict | None:
        name = (raw.get("title") or "").strip()
        if not name or len(name) < 3:
            return None

        url = raw.get("url", "")
        if url and not url.startswith("http"):
            url = f"https://dev.events{url}"

        year = raw.get("_year")
        date_str = raw.get("date", "")
        # Reconstruct a rough date: "May 28-29" + year → "2025-05-28"
        start_date = None
        if date_str and year:
            import re
            from ..normalize import parse_date
            # Remove day range suffix, keep first date
            clean = re.sub(r"-\d+", "", date_str).strip()
            start_date = parse_date(f"{clean} {year}")

        return make_event(
            name=name,
            domain="conference",
            category="Developer",
            description=raw.get("description"),
            start_date=start_date,
            website_url=url,
            data_source="dev.events",
            extraction_method="crawl4ai_css_stealth",
            raw_data=raw,
        )

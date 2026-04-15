"""Luma (lu.ma) scraper — tech/startup event discovery platform.

Luma's public discover page is heavily JS-rendered. This uses crawl4ai
stealth mode to scrape the discover page.

Note: Luma has a proper API (public-api.luma.com) but it requires a
Luma Plus subscription (x-luma-api-key). If you have a Luma API key,
set LUMA_API_KEY in .env and the API-based path will be used instead.
"""
import json
import logging
import os

import httpx
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from ..base import BaseScraper
from ..normalize import make_event

logger = logging.getLogger(__name__)

STEALTH_BROWSER = BrowserConfig(
    headless=True,
    enable_stealth=True,
    user_agent_mode="random",
    viewport_width=1440,
    viewport_height=900,
)

# Luma discover pages by category
LUMA_PAGES = [
    ("https://lu.ma/discover?category=tech",        "Technology"),
    ("https://lu.ma/discover?category=ai",          "AI / Machine Learning"),
    ("https://lu.ma/discover?category=startup",     "Startup"),
    ("https://lu.ma/discover?category=science",     "Science"),
    ("https://lu.ma/discover?category=design",      "Design"),
    ("https://lu.ma/discover?category=product",     "Product"),
    ("https://lu.ma/discover?category=web3",        "Web3 / Crypto"),
    ("https://lu.ma/discover?category=business",    "Business"),
]

# Luma renders event cards with data-eventid attributes and specific class patterns
LUMA_SCHEMA = {
    "name": "events",
    "baseSelector": "div[data-eventid], a[href*='/event/'], div[class*='event-card'], "
                    "div[class*='EventCard'], div[role='article']",
    "fields": [
        {"name": "title",    "selector": "h1, h2, h3, [class*='title'], [class*='name']",
                             "type": "text"},
        {"name": "date",     "selector": "time, [class*='date'], [class*='time'], "
                                         "[class*='when'], [datetime]",
                             "type": "text"},
        {"name": "location", "selector": "[class*='location'], [class*='place'], "
                                         "[class*='venue'], [class*='city']",
                             "type": "text"},
        {"name": "hosts",    "selector": "[class*='host'], [class*='organizer'], "
                                         "[class*='author']",
                             "type": "text"},
        {"name": "url",      "selector": "a",
                             "type": "attribute", "attribute": "href"},
    ],
}

# Scroll to load more events (Luma lazy-loads)
SCROLL_JS = """
    for (let i = 0; i < 4; i++) {
        window.scrollTo(0, document.body.scrollHeight * (i + 1) / 4);
        await new Promise(r => setTimeout(r, 1000));
    }
"""

# ── API path (requires Luma Plus) ─────────────────────────────────────────────

LUMA_API_BASE = "https://public-api.luma.com/v1"


async def _fetch_luma_api(api_key: str) -> list[dict]:
    """Fetch events via Luma API (requires Luma Plus subscription)."""
    raw_events = []
    headers = {"x-luma-api-key": api_key}
    cursor = None
    limit = 100

    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        for _ in range(50):  # max 50 pages = 5000 events
            params: dict = {"pagination_limit": limit, "sort_column": "start_at",
                            "sort_direction": "asc"}
            if cursor:
                params["pagination_cursor"] = cursor

            try:
                resp = await client.get(f"{LUMA_API_BASE}/calendar/list-events", params=params)
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.warning(f"[luma_api] HTTP {e.response.status_code}")
                break
            except httpx.RequestError as e:
                logger.warning(f"[luma_api] Request error: {e}")
                break

            data = resp.json()
            entries = data.get("entries", [])
            if not entries:
                break

            raw_events.extend(entries)
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

    logger.info(f"[luma_api] Fetched {len(raw_events)} events via API")
    return raw_events


# ── helpers ───────────────────────────────────────────────────────────────────

def _parse_luma_location(raw: str | None) -> tuple[str | None, str | None]:
    if not raw:
        return None, None
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    return raw.strip(), None


# ── scraper ───────────────────────────────────────────────────────────────────

class LumaScraper(BaseScraper):
    source_name = "luma"
    max_concurrent = 2

    async def scrape(self, **kwargs) -> list[dict]:
        api_key = os.environ.get("LUMA_API_KEY", "")

        # Use API if key is available (Luma Plus)
        if api_key:
            logger.info("[luma] Using Luma Plus API")
            events = await _fetch_luma_api(api_key)
            for e in events:
                e["_source"] = "api"
            return events

        # Fall back to CSS scraping of public discover pages
        logger.info("[luma] No LUMA_API_KEY — falling back to CSS scraping")
        return await self._scrape_css()

    async def _scrape_css(self) -> list[dict]:
        config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(schema=LUMA_SCHEMA),
            cache_mode=CacheMode.BYPASS,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            js_code=SCROLL_JS,
            remove_overlay_elements=True,
            excluded_tags=["nav", "footer", "script", "style"],
            page_timeout=60000,
        )

        url_meta = {url: category for url, category in LUMA_PAGES}
        raw_events: list[dict] = []

        async with AsyncWebCrawler(config=STEALTH_BROWSER) as crawler:
            for i in range(0, len(LUMA_PAGES), self.max_concurrent):
                batch = LUMA_PAGES[i: i + self.max_concurrent]
                urls = [url for url, _ in batch]
                results = await crawler.arun_many(
                    urls, config=config, max_concurrent=self.max_concurrent
                )

                for result in results:
                    result_url = getattr(result, "url", None) or getattr(result, "request_url", None)
                    category = url_meta.get(result_url)
                    if category is None:
                        for u in urls:
                            if result_url and u.rstrip("/") == result_url.rstrip("/"):
                                category = url_meta.get(u)
                                break
                    if category is None:
                        logger.warning(f"[{self.source_name}] Cannot match URL: {result_url}")
                        continue

                    if not result.success or not result.extracted_content:
                        logger.warning(f"[{self.source_name}] No content: {category}")
                        continue
                    try:
                        data = json.loads(result.extracted_content)
                        for item in (data if isinstance(data, list) else []):
                            item["_category"] = category
                            item["_source"] = "css"
                        raw_events.extend(data if isinstance(data, list) else [])
                        logger.info(f"[{self.source_name}] {category} → {len(data)} items")
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"[{self.source_name}] Parse error: {category}")

        return raw_events

    def normalize(self, raw: dict) -> dict | None:
        # API response shape (Luma Plus)
        if raw.get("_source") == "api":
            name = (raw.get("name") or "").strip()
            if not name:
                return None
            geo = raw.get("geo_address_info") or {}
            city, country = _parse_luma_location(geo.get("full_address"))
            return make_event(
                name=name,
                domain="conference",
                category="Technology",
                start_date=(raw.get("start_at") or "")[:10] or None,
                end_date=(raw.get("end_at") or "")[:10] or None,
                city=city,
                country=country,
                website_url=raw.get("url"),
                data_source="luma",
                extraction_method="luma_api_v1",
                raw_data={"id": raw.get("api_id"), "tags": raw.get("tags", [])},
            )

        # CSS scrape response shape
        name = (raw.get("title") or "").strip()
        if not name or len(name) < 3:
            return None

        url = raw.get("url", "")
        if url and not url.startswith("http"):
            url = f"https://lu.ma{url}"

        city, country = _parse_luma_location(raw.get("location"))

        from ..normalize import parse_date
        start_date = parse_date(raw.get("date", ""))

        return make_event(
            name=name,
            domain="conference",
            category=raw.get("_category", "Technology"),
            start_date=start_date,
            city=city,
            country=country,
            website_url=url,
            data_source="luma",
            extraction_method="crawl4ai_css_stealth",
            raw_data={k: v for k, v in raw.items() if not k.startswith("_")},
        )

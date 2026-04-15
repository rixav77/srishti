"""Shared two-phase crawl base for Indian event sites.


Phase 1 — Discovery:
    Crawl listing/home pages, execute JS to trigger lazy loading,
    then collect all internal links matching the site's event-URL pattern.

Phase 2 — Extraction:
    arun_many() over discovered URLs.  Two modes available per scraper:

    CSS mode  (use_markdown=False, default):
        Uses JsonCssExtractionStrategy with the per-site `event_schema`.
        Works when the site has stable CSS classes or semantic HTML.

    Markdown mode (use_markdown=True):
        Fetches pages without extraction strategy, then calls
        `_parse_raw_page(url, markdown, html)` which subclasses override.
        Best for React/Next.js sites using hashed styled-component classes.
"""
import json
import logging
import re
from urllib.parse import urljoin, urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from ..base import BaseScraper

logger = logging.getLogger(__name__)

STEALTH_BROWSER = BrowserConfig(
    headless=True,
    enable_stealth=True,
    user_agent_mode="random",
    viewport_width=1440,
    viewport_height=900,
)

# JS: scroll repeatedly to trigger lazy-loaded event cards
SCROLL_TO_LOAD = """
    let prevHeight = 0;
    for (let i = 0; i < 6; i++) {
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 1500));
        if (document.body.scrollHeight === prevHeight) break;
        prevHeight = document.body.scrollHeight;
    }
"""


class TwoPhaseEventScraper(BaseScraper):
    """
    Subclasses must set:
      listing_urls    : list[str]  — pages to crawl for link discovery
      event_url_re    : str        — regex that matches event detail page URLs
      currency        : str        — "INR", "USD", etc.
      country         : str        — fallback country name

    CSS mode (default, use_markdown=False):
      event_schema    : dict       — JsonCssExtractionStrategy schema

    Markdown mode (use_markdown=True):
      Override _parse_raw_page(url, markdown, html) -> dict | None
    """
    listing_urls: list[str] = []
    event_url_re: str = r"https?://.+"
    event_schema: dict = {}
    currency: str = "INR"
    country: str = "India"
    max_concurrent: int = 3
    use_markdown: bool = False      # set True for React/styled-component sites
    detail_wait_for: str | None = None  # e.g. "css:h1" to wait for element before scraping

    # ── Phase 1: discover event URLs ──────────────────────────────────────────

    async def _discover_event_urls(self, crawler: AsyncWebCrawler) -> list[str]:
        """Crawl listing pages, collect all links matching event_url_re."""
        discover_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            js_code=SCROLL_TO_LOAD,
            remove_overlay_elements=True,
            excluded_tags=["nav", "footer", "script", "style"],
            page_timeout=50000,
        )

        discovered: set[str] = set()
        pattern = re.compile(self.event_url_re)

        for listing_url in self.listing_urls:
            try:
                result = await crawler.arun(listing_url, config=discover_config)
            except Exception as exc:
                logger.warning(f"[{self.source_name}] Discovery failed for {listing_url}: {exc}")
                continue

            if not result.success:
                logger.warning(f"[{self.source_name}] Discovery request failed: {listing_url}")
                continue

            # Collect all internal (and same-domain external) links
            all_links = (
                result.links.get("internal", [])
                + result.links.get("external", [])
            )
            before = len(discovered)
            for link in all_links:
                href = (link.get("href") or "").strip()
                if not href:
                    continue
                # Resolve relative URLs against the listing page base
                if href.startswith("/") or (not href.startswith("http")):
                    parsed = urlparse(listing_url)
                    href = urljoin(f"{parsed.scheme}://{parsed.netloc}", href)
                if pattern.match(href):
                    discovered.add(href)

            logger.info(
                f"[{self.source_name}] {listing_url} → "
                f"{len(discovered) - before} new event URLs "
                f"({len(all_links)} total links scanned)"
            )

        return list(discovered)

    # ── Phase 2a: CSS extraction ───────────────────────────────────────────────

    async def _extract_events_css(
        self, crawler: AsyncWebCrawler, event_urls: list[str]
    ) -> list[dict]:
        """Scrape each event URL with the site's CSS extraction schema."""
        detail_config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(schema=self.event_schema),
            cache_mode=CacheMode.BYPASS,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            remove_overlay_elements=True,
            excluded_tags=["nav", "footer", "script", "style"],
            page_timeout=30000,
        )

        raw_events: list[dict] = []
        url_set = set(event_urls)

        for i in range(0, len(event_urls), self.max_concurrent):
            batch = event_urls[i: i + self.max_concurrent]
            try:
                results = await crawler.arun_many(
                    batch, config=detail_config, max_concurrent=self.max_concurrent
                )
            except Exception as exc:
                logger.warning(f"[{self.source_name}] Batch scrape error: {exc}")
                continue

            for result in results:
                result_url = (
                    getattr(result, "url", None)
                    or getattr(result, "request_url", None)
                    or ""
                )
                matched_url = result_url.rstrip("/")
                if matched_url not in {u.rstrip("/") for u in url_set}:
                    matched_url = next(
                        (u for u in url_set if u.rstrip("/") in result_url), None
                    )
                    if not matched_url:
                        continue

                if not result.success or not result.extracted_content:
                    continue

                try:
                    data = json.loads(result.extracted_content)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item:
                            item["_source_url"] = result_url
                            raw_events.append(item)
                except (json.JSONDecodeError, TypeError):
                    logger.debug(f"[{self.source_name}] Parse error: {result_url}")

        return raw_events

    # ── Phase 2b: Markdown extraction ─────────────────────────────────────────

    async def _extract_events_markdown(
        self, crawler: AsyncWebCrawler, event_urls: list[str]
    ) -> list[dict]:
        """Fetch pages as markdown+HTML; call _parse_raw_page() per result."""
        detail_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            remove_overlay_elements=True,
            page_timeout=30000,
            **({"wait_for": self.detail_wait_for} if self.detail_wait_for else {}),
        )

        raw_events: list[dict] = []
        url_set = set(event_urls)

        for i in range(0, len(event_urls), self.max_concurrent):
            batch = event_urls[i: i + self.max_concurrent]
            try:
                results = await crawler.arun_many(
                    batch, config=detail_config, max_concurrent=self.max_concurrent
                )
            except Exception as exc:
                logger.warning(f"[{self.source_name}] Batch error: {exc}")
                continue

            for result in results:
                result_url = (
                    getattr(result, "url", None)
                    or getattr(result, "request_url", None)
                    or ""
                )
                matched_url = result_url.rstrip("/")
                if matched_url not in {u.rstrip("/") for u in url_set}:
                    matched_url = next(
                        (u for u in url_set if u.rstrip("/") in result_url), None
                    )
                    if not matched_url:
                        continue

                if not result.success:
                    logger.debug(f"[{self.source_name}] Failed: {result_url}")
                    continue

                try:
                    raw = self._parse_raw_page(
                        url=result_url,
                        markdown=result.markdown or "",
                        html=result.html or "",
                    )
                    if raw:
                        raw["_source_url"] = result_url
                        raw_events.append(raw)
                except Exception as exc:
                    logger.debug(f"[{self.source_name}] Parse error {result_url}: {exc}")

        return raw_events

    def _parse_raw_page(self, url: str, markdown: str, html: str) -> dict | None:
        """
        Override in markdown-mode subclasses.
        Return a raw dict (same keys as CSS schema fields) or None to skip.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _parse_raw_page() "
            "when use_markdown=True"
        )

    # ── Phase 2 router ────────────────────────────────────────────────────────

    async def _extract_events(
        self, crawler: AsyncWebCrawler, event_urls: list[str]
    ) -> list[dict]:
        if not event_urls:
            return []
        if self.use_markdown:
            return await self._extract_events_markdown(crawler, event_urls)
        return await self._extract_events_css(crawler, event_urls)

    # ── orchestrate ───────────────────────────────────────────────────────────

    async def scrape(self, **kwargs) -> list[dict]:
        async with AsyncWebCrawler(config=STEALTH_BROWSER) as crawler:
            event_urls = await self._discover_event_urls(crawler)
            logger.info(
                f"[{self.source_name}] Discovered {len(event_urls)} event URLs "
                f"across {len(self.listing_urls)} listing page(s)"
            )
            if not event_urls:
                logger.warning(f"[{self.source_name}] No event URLs found — bot blocked?")
                return []
            return await self._extract_events(crawler, event_urls)

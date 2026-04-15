"""BookMyShow scraper — India's largest event ticketing platform.

Covers movies, concerts, sports, comedy, theatre across all Indian cities.

Strategy:
  Phase 1 — crawl the homepage + main events/concerts/sports pages,
             collect all event detail links discovered in HTML
  Phase 2 — scrape each individual event page as markdown + HTML.
             BMS uses hashed styled-component classes (e.g. sc-1qdowf4-0 dpaUna),
             so CSS selectors are unreliable.  Instead we parse:
               • result.markdown for title / date / genre / venue
               • result.html     for ₹-prefixed price spans

BookMyShow event URLs follow the pattern:
  https://in.bookmyshow.com/buytickets/[event-name]/ET[id]
  https://in.bookmyshow.com/sports/[event-slug]/ET[id]
  https://in.bookmyshow.com/concerts/[event-slug]/ET[id]
"""
import logging
import re

from ..normalize import make_event
from .base_crawl import TwoPhaseEventScraper

logger = logging.getLogger(__name__)

# ── listing pages ─────────────────────────────────────────────────────────────

BMS_LISTING_URLS = [
    # Explore pages discovered individually (fresh session per page).
    # Omit the homepage — it doesn't yield many event links and its
    # Cloudflare session cookie poisons subsequent explore-page requests.
    "https://in.bookmyshow.com/explore/events-mumbai",
    "https://in.bookmyshow.com/explore/events-delhi-ncr",
    "https://in.bookmyshow.com/explore/events-bengaluru",
    "https://in.bookmyshow.com/explore/events-hyderabad",
    "https://in.bookmyshow.com/explore/events-chennai",
    "https://in.bookmyshow.com/explore/concerts-mumbai",
    "https://in.bookmyshow.com/explore/concerts-delhi-ncr",
    "https://in.bookmyshow.com/explore/sports-mumbai",
]

# BookMyShow event page URL patterns:
#   /buytickets/...    concerts, theatre, comedy events
#   /sports/...        sports events
#   /concerts/...      sometimes concerts have their own path
# All contain an event code like ET[0-9A-Z]+
BMS_EVENT_URL_RE = (
    r"https://(?:in\.)?bookmyshow\.com/"
    r"(?:buytickets|sports|concerts|events)/[^/?#]+"
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _after_icon(markdown: str, icon_name: str) -> str:
    """
    BMS markdown encodes metadata with CDN icon images, e.g.:
      ![](..calendar.png) Thu 30 Apr 2026 ![](..time.png) 5:00 PM ...

    Returns the text between `icon_name` marker and the next `![]` or end.
    """
    pattern = re.compile(
        rf"!\[.*?\]\([^)]*{re.escape(icon_name)}[^)]*\)\s*(.*?)(?=!\[|$)",
        re.DOTALL,
    )
    m = pattern.search(markdown)
    if not m:
        return ""
    return m.group(1).strip().split("\n")[0].strip()


def _parse_inr_html(html: str) -> tuple[float | None, float | None]:
    """Extract ₹-prefixed prices from raw HTML (works despite hashed class names)."""
    prices = []
    for raw in re.findall(r"₹\s*([\d,]+(?:\.\d{2})?)", html):
        try:
            prices.append(float(raw.replace(",", "")))
        except ValueError:
            pass
    if not prices:
        # Fallback: look for "onwards" / "upwards" phrase
        m = re.search(r"(?:starts?|from|onwards?|upwards?)\s*(?:at\s*)?₹\s*([\d,]+)", html)
        if m:
            try:
                v = float(m.group(1).replace(",", ""))
                return v, v
            except ValueError:
                pass
        return None, None
    prices.sort()
    return prices[0], prices[-1]


def _extract_title_from_markdown(markdown: str) -> str:
    """First H1 or H2 line in markdown, stripped."""
    for line in markdown.splitlines():
        stripped = line.lstrip("#").strip()
        if line.startswith("# ") or line.startswith("## "):
            if stripped and len(stripped) > 2:
                return stripped
    return ""


def _extract_location_bms(location_text: str) -> tuple[str | None, str | None]:
    """
    BMS location text is typically:  "Venue Name: City"  or  "Venue Name, City"
    Returns (venue, city).
    """
    if not location_text:
        return None, None
    # colon separator  e.g. "Jio World Garden, BKC: Mumbai"
    if ":" in location_text:
        parts = location_text.rsplit(":", 1)
        venue = parts[0].strip() or None
        city  = parts[1].strip() or None
        return venue, city
    # comma separator — last element is city
    if "," in location_text:
        parts = [p.strip() for p in location_text.rsplit(",", 1)]
        return parts[0] or None, parts[1] or None
    return location_text.strip() or None, None


# ── scraper ───────────────────────────────────────────────────────────────────

class BookMyShowScraper(TwoPhaseEventScraper):
    source_name      = "bookmyshow"
    listing_urls     = BMS_LISTING_URLS
    event_url_re     = BMS_EVENT_URL_RE
    currency         = "INR"
    country          = "India"
    max_concurrent   = 2   # BMS has stricter rate limits
    use_markdown     = True
    detail_wait_for  = "css:h1"

    async def scrape(self, **kwargs) -> list[dict]:
        """
        Override to use a fresh browser session per listing/detail batch.
        BMS Cloudflare blocks multi-page sessions; separate sessions avoid it.
        """
        from .base_crawl import AsyncWebCrawler, STEALTH_BROWSER, CrawlerRunConfig, CacheMode
        import asyncio as _asyncio

        # ── Phase 1: discover (one fresh session per listing URL) ──────────
        discovered: set[str] = set()
        for listing_url in self.listing_urls:
            async with AsyncWebCrawler(config=STEALTH_BROWSER) as crawler:
                saved = self.listing_urls
                self.listing_urls = [listing_url]
                urls = await self._discover_event_urls(crawler)
                self.listing_urls = saved
                discovered.update(urls)
            await _asyncio.sleep(1.5)

        event_urls = list(discovered)
        logger.info(
            f"[{self.source_name}] Discovered {len(event_urls)} event URLs "
            f"across {len(self.listing_urls)} listing page(s)"
        )
        if not event_urls:
            logger.warning(f"[{self.source_name}] No event URLs found — bot blocked?")
            return []

        # ── Phase 2: extract (fresh session per small batch) ───────────────
        detail_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            remove_overlay_elements=True,
            page_timeout=30000,
            wait_for=self.detail_wait_for,
        )

        raw_events: list[dict] = []
        batch_size = 3   # fresh browser every 3 BMS pages to avoid Cloudflare

        for i in range(0, len(event_urls), batch_size):
            batch = event_urls[i: i + batch_size]
            async with AsyncWebCrawler(config=STEALTH_BROWSER) as crawler:
                try:
                    results = await crawler.arun_many(
                        batch, config=detail_config, max_concurrent=2
                    )
                except Exception as exc:
                    logger.warning(f"[{self.source_name}] Batch error: {exc}")
                    continue

            for result in results:
                result_url = getattr(result, "url", None) or getattr(result, "request_url", None) or ""
                if not result.success:
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

            await _asyncio.sleep(2.0)   # inter-batch delay

        return raw_events

    # ── markdown parser ───────────────────────────────────────────────────────

    def _parse_raw_page(self, url: str, markdown: str, html: str) -> dict | None:
        title = _extract_title_from_markdown(markdown)
        if not title:
            # Try og:title from HTML
            m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', html)
            if m:
                title = m.group(1).strip()
        if not title or len(title) < 3:
            return None

        date_text  = _after_icon(markdown, "calendar")
        genre_text = _after_icon(markdown, "genre")
        loc_text   = _after_icon(markdown, "location")

        venue, city = _extract_location_bms(loc_text)

        price_min, price_max = _parse_inr_html(html)

        return {
            "title":    title,
            "date":     date_text,
            "category": genre_text,
            "venue":    venue,
            "city":     city,
            "price":    f"₹{price_min}" if price_min is not None else "",
            "_price_min": price_min,
            "_price_max": price_max,
        }

    # ── normalise ─────────────────────────────────────────────────────────────

    def normalize(self, raw: dict) -> dict | None:
        name = (raw.get("title") or "").strip()
        if not name or len(name) < 3:
            return None

        from ..normalize import parse_date
        start_date = parse_date(raw.get("date") or "")

        price_min = raw.get("_price_min")
        price_max = raw.get("_price_max")

        venue = (raw.get("venue") or "").strip() or None
        city  = (raw.get("city")  or "").strip() or None

        raw_cat    = (raw.get("category") or "").lower()
        source_url = raw.get("_source_url", "")

        if any(w in raw_cat for w in ("concert", "music", "festival", "live", "gig")):
            domain = "music_festival"
        elif any(w in (raw_cat + source_url) for w in ("sport", "cricket", "football", "ipl")):
            domain = "sporting_event"
        else:
            domain = "conference"

        return make_event(
            name=name,
            domain=domain,
            category=raw.get("category") or "Events",
            description=None,
            start_date=start_date,
            city=city,
            country=self.country,
            venue_name=venue,
            ticket_price_min=price_min,
            ticket_price_max=price_max,
            currency=self.currency,
            website_url=source_url,
            data_source="bookmyshow",
            extraction_method="crawl4ai_markdown",
            raw_data={k: v for k, v in raw.items() if not k.startswith("_")},
        )

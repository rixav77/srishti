"""Skillboxes.com scraper — Indian live entertainment ticketing platform.

Covers concerts, festivals, comedy, arts events across Indian cities.
Major events: VH1 Supersonic, K-Wave Festival, Dream Theater tours, etc.

Strategy:
  Phase 1 — crawl https://www.skillboxes.com/events,
             collect all /events/[slug] links (including /events/ticket/[slug])
  Phase 2 — scrape each event detail page.
             Skillboxes renders via React with client-side hydration; pages
             need `wait_for="css:h1"` to load content.  Markdown is then clean:

               # EVENT TITLE
               25 April 2026 | 05:00 PM Onwards
               RROV,  Goa
               Club Gigs - Music
               Book Now
               INR 3333 - 18000

             We parse title / date / venue / city / category / price from this
             structured markdown without relying on CSS class names.
"""
import re

from ..normalize import make_event, classify_event
from .base_crawl import TwoPhaseEventScraper

# ── listing pages ─────────────────────────────────────────────────────────────

SKILLBOXES_LISTING_URLS = [
    "https://www.skillboxes.com/events",
    "https://www.skillboxes.com/events-bangalore",
    "https://www.skillboxes.com/events-mumbai",
    "https://www.skillboxes.com/events-new-delhi",
    "https://www.skillboxes.com/events-hyderabad",
    "https://www.skillboxes.com/events-pune",
    "https://www.skillboxes.com/events-kolkata",
    "https://www.skillboxes.com/events-chennai",
]

# Event pages: /events/[slug]  or  /events/ticket/[slug]
# After relative-URL resolution these become absolute skillboxes.com URLs.
SKILLBOXES_EVENT_URL_RE = (
    r"https://(?:www\.)?skillboxes\.com/events/"
    r"(?:ticket/)?[^/?#]+"
)


# ── helpers ───────────────────────────────────────────────────────────────────

# Date pattern: "25 April 2026" / "25 Apr 2026" / "April 25, 2026"
_DATE_RE = re.compile(
    r"\b(?:\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+20\d{2}"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+20\d{2}"
    r"|\d{1,2}/\d{1,2}/20\d{2})\b",
    re.IGNORECASE,
)

# Price pattern: "INR 3333 - 18000" / "INR 3333" / "₹3333 - ₹18000"
_PRICE_RE = re.compile(
    r"(?:INR|₹)\s*([\d,]+)\s*[-–to]+\s*(?:INR|₹)?\s*([\d,]+)"
    r"|(?:INR|₹)\s*([\d,]+)",
    re.IGNORECASE,
)


def _parse_price(line: str) -> tuple[float | None, float | None]:
    m = _PRICE_RE.search(line)
    if not m:
        return None, None
    if m.group(1) and m.group(2):
        return float(m.group(1).replace(",", "")), float(m.group(2).replace(",", ""))
    v = m.group(3)
    if v:
        f = float(v.replace(",", ""))
        return f, f
    return None, None


def _extract_from_skillboxes_markdown(markdown: str) -> dict:
    """
    Parse the clean Skillboxes event markdown structure.
    Lines immediately after the H1 heading contain: date, venue, category, price.
    """
    lines = [l.strip() for l in markdown.splitlines() if l.strip()]
    title = ""
    h1_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line.lstrip("# ").strip()
            h1_idx = i
            break

    if not title or h1_idx < 0:
        return {}

    # Look at the ~8 lines after H1 for structured metadata
    block = lines[h1_idx + 1: h1_idx + 10]

    date_text = ""
    venue = None
    city  = None
    category = ""
    price_min = None
    price_max = None

    for line in block:
        if not date_text:
            m = _DATE_RE.search(line)
            if m:
                date_text = m.group(0)
                continue

        if not venue:
            # Venue line: "RROV, Goa" — contains a comma, is not a price, not a date
            if "," in line and not _DATE_RE.search(line) and "INR" not in line.upper() and "₹" not in line:
                parts = [p.strip() for p in line.split(",")]
                venue = parts[0] or None
                city  = parts[1] if len(parts) > 1 else None
                continue

        if not category:
            # Category lines: "Club Gigs - Music", "Electronic Dance Music", etc.
            if (
                re.search(r"\b(music|dance|comedy|sport|festival|arts?|workshop|yoga)\b", line, re.IGNORECASE)
                and "INR" not in line.upper() and "₹" not in line
                and not _DATE_RE.search(line)
                and "Book" not in line
            ):
                category = line
                continue

        if price_min is None:
            p_min, p_max = _parse_price(line)
            if p_min is not None:
                price_min, price_max = p_min, p_max

    return {
        "title":      title,
        "date":       date_text,
        "venue":      venue,
        "city":       city,
        "category":   category,
        "_price_min": price_min,
        "_price_max": price_max,
    }


# ── scraper ───────────────────────────────────────────────────────────────────

class SkillboxesScraper(TwoPhaseEventScraper):
    source_name    = "skillboxes"
    listing_urls   = SKILLBOXES_LISTING_URLS
    event_url_re   = SKILLBOXES_EVENT_URL_RE
    currency       = "INR"
    country        = "India"
    max_concurrent = 3
    use_markdown   = True
    detail_wait_for = "css:h1"   # wait for React hydration

    # ── markdown parser ───────────────────────────────────────────────────────

    def _parse_raw_page(self, url: str, markdown: str, html: str) -> dict | None:
        raw = _extract_from_skillboxes_markdown(markdown)
        if not raw or not raw.get("title"):
            return None
        return raw

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

        domain, category_label, subcategory = classify_event(
            name=name,
            description="",
            category=raw.get("category") or "",
            source_url=raw.get("_source_url", ""),
        )

        return make_event(
            name=name,
            domain=domain,
            category=category_label,
            subcategory=subcategory,
            description=None,
            start_date=start_date,
            city=city,
            country=self.country,
            venue_name=venue,
            ticket_price_min=price_min,
            ticket_price_max=price_max,
            currency=self.currency,
            website_url=raw.get("_source_url"),
            data_source="skillboxes",
            extraction_method="crawl4ai_markdown",
            raw_data={k: v for k, v in raw.items() if not k.startswith("_")},
        )

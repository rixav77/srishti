"""Mepass.in scraper — Indian event ticketing platform.

~1,632 events across Indian cities. Covers concerts, comedy, sports,
festivals, workshops.

Strategy:
  Phase 1 — crawl https://www.mepass.in/events (+ category sub-pages),
             collect all /events/[slug] links
  Phase 2 — scrape each event detail page as markdown + HTML.
             Mepass uses Next.js; dates/prices are embedded in HTML as
             ISO dates and ₹ spans — extracted via regex on result.html.
"""
import re

from ..normalize import make_event, classify_event
from .base_crawl import TwoPhaseEventScraper

# ── listing pages ─────────────────────────────────────────────────────────────

MEPASS_LISTING_URLS = [
    "https://www.mepass.in/events",
]

# Event detail URLs look like: https://www.mepass.in/events/some-event-slug
MEPASS_EVENT_URL_RE = r"https://(?:www\.)?mepass\.in/events/[^/?#]+"


# ── helpers ───────────────────────────────────────────────────────────────────

def _extract_iso_date(html: str) -> str | None:
    """Find the first ISO date (2025-/2026-) in the HTML."""
    m = re.search(r"(202[5-9]-\d{2}-\d{2})", html)
    return m.group(1) if m else None


def _extract_inr_html(html: str) -> tuple[float | None, float | None]:
    """
    Extract ₹-prefixed prices from raw HTML.
    Mepass renders price as: <span ...>₹799</span><span ...>onwards</span>
    """
    # Try ₹ unicode character (U+20B9)
    prices = []
    for raw in re.findall(r"₹\s*([\d,]+(?:\.\d{2})?)", html):
        try:
            prices.append(float(raw.replace(",", "")))
        except ValueError:
            pass
    if not prices:
        # HTML entity fallbacks
        for raw in re.findall(r"(?:&#8377;|&rupee;)\s*([\d,]+)", html):
            try:
                prices.append(float(raw.replace(",", "")))
            except ValueError:
                pass
    if not prices:
        # Embedded in JSON-ish strings: original_price\":799 or \"price\":799.00
        for raw in re.findall(r'"(?:original_price|price)\\?":\\"?([\d.]+)\\"?', html):
            try:
                v = float(raw)
                if v > 0:
                    prices.append(v)
            except ValueError:
                pass
    if not prices:
        return None, None
    prices.sort()
    return prices[0], prices[-1]


def _extract_title_from_markdown(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# ") or line.startswith("## "):
            stripped = line.lstrip("#").strip()
            if stripped and len(stripped) > 2:
                return stripped
    return ""


_KNOWN_CITIES = {
    "mumbai", "delhi", "new delhi", "bengaluru", "bangalore", "hyderabad",
    "chennai", "pune", "kolkata", "ahmedabad", "jaipur", "lucknow",
    "chandigarh", "indore", "bhopal", "nagpur", "surat", "vadodara",
    "kochi", "thiruvananthapuram", "gurgaon", "gurugram", "noida", "goa",
    "agra", "varanasi", "patna", "ranchi", "bhubaneswar", "coimbatore",
    "visakhapatnam", "vijayawada", "mysuru", "mysore",
}


def _extract_venue_from_markdown(markdown: str) -> tuple[str | None, str | None]:
    """
    Mepass renders:
      ### Venue
      Dr. B.R. Ambedkar Auditorium, Lucknow, Uttar Pradesh
    Returns (venue, city).
    City is taken from the first recognisable city in the comma-separated parts.
    """
    lines = markdown.splitlines()
    for i, line in enumerate(lines):
        if re.search(r"#+\s*venue", line, re.IGNORECASE):
            for j in range(i + 1, min(i + 5, len(lines))):
                venue_line = lines[j].strip()
                if venue_line and not venue_line.startswith("#") and not venue_line.startswith("!"):
                    parts = [p.strip() for p in venue_line.split(",")]
                    venue = parts[0] if parts else venue_line
                    city  = None
                    # Look for a known city in the parts (skip the venue name itself)
                    for part in parts[1:]:
                        if part.lower() in _KNOWN_CITIES:
                            city = part.title()
                            break
                    # Fallback: use second part if no known city found
                    if city is None and len(parts) > 1:
                        city = parts[1] if len(parts[1]) <= 30 else None
                    return venue or None, city or None
    return None, None


# ── scraper ───────────────────────────────────────────────────────────────────

class MepassScraper(TwoPhaseEventScraper):
    source_name    = "mepass"
    listing_urls   = MEPASS_LISTING_URLS
    event_url_re   = MEPASS_EVENT_URL_RE
    currency       = "INR"
    country        = "India"
    max_concurrent = 4
    use_markdown   = True

    # ── page parser ───────────────────────────────────────────────────────────

    def _parse_raw_page(self, url: str, markdown: str, html: str) -> dict | None:
        title = _extract_title_from_markdown(markdown)
        if not title:
            # Fallback: og:title meta
            m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', html)
            if m:
                title = m.group(1).strip()
        if not title or len(title) < 3:
            return None

        date_text  = _extract_iso_date(html)
        price_min, price_max = _extract_inr_html(html)
        venue, city = _extract_venue_from_markdown(markdown)

        return {
            "title":      title,
            "date":       date_text,
            "venue":      venue,
            "city":       city,
            "_price_min": price_min,
            "_price_max": price_max,
            "category":   "",
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
        if not city and venue and "," in venue:
            parts = [p.strip() for p in venue.split(",")]
            city = parts[-1]

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
            data_source="mepass",
            extraction_method="crawl4ai_markdown",
            raw_data={k: v for k, v in raw.items() if not k.startswith("_")},
        )

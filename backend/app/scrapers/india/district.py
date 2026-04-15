"""District (by Zomato) scraper — Indian event discovery and ticketing platform.

Covers movies, concerts, sports, plays, comedy, activities across Indian cities.

Strategy:
  Phase 1 — crawl https://www.district.in/ and city-specific event pages,
             follow all event detail links found in HTML
  Phase 2 — scrape each individual event page as markdown + HTML.
             District uses Next.js with auto-generated CSS class names,
             so we parse result.markdown and look for JSON-LD / og: meta
             as fallback signals.

District event URLs follow the pattern:
  https://www.district.in/[city]/events/[event-slug]
  https://www.district.in/events/[event-slug]
"""
import json
import re

from ..normalize import make_event, classify_event
from .base_crawl import TwoPhaseEventScraper

# ── listing pages ─────────────────────────────────────────────────────────────

DISTRICT_LISTING_URLS = [
    # General pages
    "https://www.district.in/",
    "https://www.district.in/events/",
    # City pages
    "https://www.district.in/mumbai/events/",
    "https://www.district.in/delhi/events/",
    "https://www.district.in/bengaluru/events/",
    "https://www.district.in/hyderabad/events/",
    "https://www.district.in/chennai/events/",
    "https://www.district.in/pune/events/",
    "https://www.district.in/kolkata/events/",
    "https://www.district.in/ahmedabad/events/",
    "https://www.district.in/goa/events/",
    "https://www.district.in/noida/events/",
    "https://www.district.in/gurgaon/events/",
    # Sports category pages
    "https://www.district.in/events/ipl-ticket-booking",
    "https://www.district.in/events/sports-events-in-new-delhi-book-tickets",
    "https://www.district.in/events/sports-events-in-mumbai-book-tickets",
    "https://www.district.in/events/sports-events-in-bengaluru-book-tickets",
    "https://www.district.in/events/sports-events-in-pune-book-tickets",
    # Music category pages (city variants)
    "https://www.district.in/events/music-in-new-delhi-book-tickets",
    "https://www.district.in/events/music-in-mumbai-book-tickets",
    "https://www.district.in/events/music-in-bengaluru-book-tickets",
    "https://www.district.in/events/music-in-pune-book-tickets",
    "https://www.district.in/events/music-in-hyderabad-book-tickets",
    "https://www.district.in/events/music-in-goa-book-tickets",
    "https://www.district.in/events/music-in-kolkata-book-tickets",
    "https://www.district.in/events/music-in-chennai-book-tickets",
]

# Only match individual event detail pages (end with -buy-tickets).
# Category/collection pages end with -book-tickets or -ticket-booking
# and are used as listing pages above, not scraped as individual events.
DISTRICT_EVENT_URL_RE = (
    r"https://(?:www\.)?district\.in/"
    r"(?:[a-z-]+/)?events/[^/?#]+-buy-tickets"
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _parse_inr(text: str) -> tuple[float | None, float | None]:
    if not text:
        return None, None
    low = text.lower()
    if "free" in low:
        return 0.0, 0.0
    clean = re.sub(r"[₹Rs.\s,]", "", text)
    nums = sorted({float(n) for n in re.findall(r"\d+(?:\.\d+)?", clean) if float(n) > 0})
    if not nums:
        return None, None
    return nums[0], nums[-1]


def _parse_inr_html(html: str) -> tuple[float | None, float | None]:
    """Extract ₹-prefixed prices from raw HTML."""
    prices = []
    for raw in re.findall(r"₹\s*([\d,]+(?:\.\d{2})?)", html):
        try:
            prices.append(float(raw.replace(",", "")))
        except ValueError:
            pass
    if not prices:
        return None, None
    prices.sort()
    return prices[0], prices[-1]


def _extract_json_ld(html: str) -> dict | None:
    """Try to extract Event schema from JSON-LD script tag."""
    for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL):
        try:
            data = json.loads(raw.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") in ("Event", "MusicEvent", "SportsEvent"):
                    return item
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _og_meta(html: str, prop: str) -> str:
    m = re.search(
        rf'<meta[^>]+(?:property|name)=["\'](?:og:)?{re.escape(prop)}["\'][^>]+content=["\'](.*?)["\']',
        html,
    )
    return m.group(1).strip() if m else ""


def _extract_title_from_markdown(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# ") or line.startswith("## "):
            stripped = line.lstrip("#").strip()
            if stripped and len(stripped) > 2:
                return stripped
    return ""


def _extract_date_from_markdown(markdown: str) -> str:
    """
    Look for date-like patterns in markdown text.
    District renders dates in formats like:
      "Sat, 19 Apr 2025"  /  "19 April 2025"  /  "Apr 19, 2025"
    """
    patterns = [
        r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+20\d{2}\b",
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+20\d{2}\b",
        r"\b\d{1,2}/\d{1,2}/20\d{2}\b",
    ]
    for pat in patterns:
        m = re.search(pat, markdown)
        if m:
            return m.group(0)
    return ""


def _extract_city_from_address_str(addr: str) -> str | None:
    """
    Extract city from a flat address string like:
    "Muni Maya Ram Jain Marg, ..., Pitampura, नई दिल्ली, Delhi, 110034, India"
    Strategy: split by comma, skip postcodes and "India", return the first
    recognisable Indian city name.
    """
    if not addr:
        return None
    indian_cities = {
        "mumbai", "delhi", "new delhi", "bengaluru", "bangalore", "hyderabad",
        "chennai", "pune", "kolkata", "ahmedabad", "jaipur", "lucknow",
        "chandigarh", "indore", "bhopal", "nagpur", "surat", "vadodara",
        "kochi", "thiruvananthapuram", "gurgaon", "gurugram", "noida", "goa",
        "agra", "varanasi", "patna", "ranchi", "bhubaneswar",
    }
    parts = [p.strip() for p in addr.split(",")]
    for part in parts:
        clean = part.strip().rstrip(" 0123456789-").strip()
        if clean.lower() in indian_cities:
            return clean.title()
    return None


def _extract_city_from_url(url: str) -> str | None:
    m = re.search(r"district\.in/([a-z-]+)/events/", url)
    if m:
        city = m.group(1)
        if city not in ("events",):
            return city.replace("-", " ").title()
    return None


# ── scraper ───────────────────────────────────────────────────────────────────

class DistrictScraper(TwoPhaseEventScraper):
    source_name    = "district"
    listing_urls   = DISTRICT_LISTING_URLS
    event_url_re   = DISTRICT_EVENT_URL_RE
    currency       = "INR"
    country        = "India"
    max_concurrent = 3
    use_markdown   = True

    # ── markdown / HTML parser ────────────────────────────────────────────────

    def _parse_raw_page(self, url: str, markdown: str, html: str) -> dict | None:
        # 1. Try JSON-LD first (cleanest source)
        ld = _extract_json_ld(html)
        if ld:
            name = ld.get("name", "").strip()
            description = (ld.get("description") or "")[:500].strip()

            # District uses ISO 8601 datetimes: "2026-04-28T04:30:00.000Z"
            raw_date = ld.get("startDate", "")
            date_text = raw_date.split("T")[0] if "T" in raw_date else raw_date

            # Location — may be a dict (Place) or string
            location = ld.get("location") or {}
            venue = None
            city  = None
            if isinstance(location, dict):
                venue = location.get("name", "") or None
                addr  = location.get("address") or {}
                if isinstance(addr, dict):
                    city = (
                        addr.get("addressLocality")
                        or addr.get("addressRegion")
                        or ""
                    ).strip() or None
                elif isinstance(addr, str):
                    # Extract city from address string: "…, Delhi, 110034, India"
                    city = _extract_city_from_address_str(addr)
            else:
                venue = str(location) or None

            # Offers — schema.org Offer or AggregateOffer
            offers = ld.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            if isinstance(offers, dict):
                low  = offers.get("price") or offers.get("lowPrice")
                high = offers.get("price") or offers.get("highPrice")
                try:
                    price_min = float(low)  if low  is not None else None
                    price_max = float(high) if high is not None else None
                except (ValueError, TypeError):
                    price_min = price_max = None
            else:
                price_min = price_max = None

            if price_min is None:
                price_min, price_max = _parse_inr_html(html)

            # Category from @type
            evt_type = ld.get("@type", "Event")
            if evt_type == "MusicEvent":
                category = "music"
            elif evt_type == "SportsEvent":
                category = "sport"
            else:
                category = ld.get("eventAttendanceMode", "") or ""

            return {
                "title":       name,
                "date":        date_text,
                "venue":       venue,
                "city":        city,
                "category":    category,
                "description": description or None,
                "_price_min":  price_min,
                "_price_max":  price_max,
            }

        # 2. Fallback: parse markdown + og: meta + HTML
        title = _extract_title_from_markdown(markdown)
        if not title:
            title = _og_meta(html, "title")
        if not title or len(title) < 3:
            return None

        date_text   = _extract_date_from_markdown(markdown)
        description = (_og_meta(html, "description") or "")[:500] or None
        city        = _extract_city_from_url(url)
        price_min, price_max = _parse_inr_html(html)

        # Try to find venue — look for text near location icon or address pattern
        venue = None
        venue_m = re.search(
            r"(?:venue|location|place)[:\s]+([^\n|•·,]{5,60})",
            markdown.lower(),
        )
        if venue_m:
            venue = venue_m.group(1).strip().title()

        return {
            "title":       title,
            "date":        date_text,
            "venue":       venue,
            "city":        city,
            "category":    "",
            "description": description,
            "_price_min":  price_min,
            "_price_max":  price_max,
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
            city = venue.split(",")[-1].strip()

        # Derive city from URL if still not found
        if not city:
            city = _extract_city_from_url(raw.get("_source_url", ""))

        domain, category_label, subcategory = classify_event(
            name=name,
            description=raw.get("description") or "",
            category=raw.get("category") or "",
            source_url=raw.get("_source_url", ""),
        )

        return make_event(
            name=name,
            domain=domain,
            category=category_label,
            subcategory=subcategory,
            description=(raw.get("description") or "")[:500] or None,
            start_date=start_date,
            city=city,
            country=self.country,
            venue_name=venue,
            ticket_price_min=price_min,
            ticket_price_max=price_max,
            currency=self.currency,
            website_url=raw.get("_source_url"),
            data_source="district",
            extraction_method="crawl4ai_markdown",
            raw_data={k: v for k, v in raw.items() if not k.startswith("_")},
        )

"""Normalization utilities — convert raw scraped data to unified event schema."""
import re
from datetime import datetime


def parse_date(raw: str | None) -> str | None:
    """Try common date formats, return ISO 8601 date string or None."""
    if not raw:
        return None
    raw = raw.strip()
    formats = [
        "%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%b %d, %Y",
        "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%B %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Try extracting year at minimum
    m = re.search(r"(202[4-9])", raw)
    return f"{m.group(1)}-01-01" if m else None


def normalize_location(city: str | None, country: str | None) -> tuple[str | None, str | None]:
    """Basic cleanup for city/country strings."""
    def clean(s: str | None) -> str | None:
        if not s:
            return None
        return s.strip().title()
    return clean(city), clean(country)


def make_event(
    *,
    name: str,
    domain: str,
    category: str | None = None,
    subcategory: str | None = None,
    description: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    city: str | None = None,
    country: str | None = None,
    venue_name: str | None = None,
    estimated_attendance: int | None = None,
    ticket_price_min: float | None = None,
    ticket_price_max: float | None = None,
    currency: str = "USD",
    website_url: str | None = None,
    sponsors: list[str] | None = None,
    speakers: list[str] | None = None,
    data_source: str = "unknown",
    extraction_method: str = "crawl4ai",
    raw_data: dict | None = None,
) -> dict:
    """Build a unified event dict matching the events table schema."""
    city, country = normalize_location(city, country)
    year = None
    if start_date:
        try:
            year = int(start_date[:4])
        except (ValueError, TypeError):
            pass

    return {
        "name": name.strip(),
        "domain": domain,
        "category": category,
        "subcategory": subcategory,
        "description": description,
        "start_date": parse_date(start_date),
        "end_date": parse_date(end_date),
        "city": city,
        "country": country,
        "venue_name": venue_name,
        "estimated_attendance": estimated_attendance,
        "ticket_price_min": ticket_price_min,
        "ticket_price_max": ticket_price_max,
        "currency": currency,
        "website_url": website_url,
        "year": year,
        "sponsors": sponsors or [],
        "speakers": speakers or [],
        "data_source": data_source,
        "extraction_method": extraction_method,
        "raw_data": raw_data or {},
    }


def dedup_key(event: dict) -> str:
    name = (event.get("name") or "").lower().strip()
    year = str(event.get("year") or "")
    city = (event.get("city") or "").lower().strip()
    return f"{name}|{year}|{city}"


def dedup(events: list[dict]) -> list[dict]:
    """Remove duplicate events by (name, year, city) composite key."""
    seen: set[str] = set()
    unique = []
    for e in events:
        key = dedup_key(e)
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def is_valid(event: dict) -> bool:
    """Reject records missing mandatory fields (name + date)."""
    return bool(event.get("name")) and bool(event.get("start_date"))

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
    """Clean city/country strings; discard obviously-garbage values."""
    def clean(s: str | None) -> str | None:
        if not s:
            return None
        s = s.strip()
        # Discard year-range patterns like "2001–2019" or "2022–present"
        if re.search(r"\d{4}[–\-]", s):
            return None
        # Discard if longer than 40 chars (venue text bleed-through)
        if len(s) > 40:
            return None
        # Discard if contains colon (e.g. "Flagship:Las Vegas")
        if ":" in s:
            return None
        # Discard if contains parenthesis (venue(city) leftovers)
        if "(" in s or ")" in s:
            return None
        # Discard postcode/zip-like suffix (e.g. "Church Roadsw19", "NY 10001")
        if re.search(r"[a-z]{2}\d{1,2}$|[A-Z]{1,2}\d{1,2}$|\d{5}$", s):
            return None
        return s.title()
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


def classify_event(
    name: str = "",
    description: str = "",
    category: str = "",
    source_url: str = "",
) -> tuple[str, str, str | None]:
    """
    Return (domain, category_label, subcategory) based on text signals.

    Domains: conference | music_festival | sporting_event | comedy | workshop | entertainment
    """
    text = " ".join([name, description, category, source_url]).lower()

    # ── Sports ────────────────────────────────────────────────────────────────
    if any(w in text for w in (
        "cricket", "ipl", "football", "kabaddi", "badminton", "tennis",
        "hockey", "basketball", "marathon", "run ", "running", "cycling",
        "swimming", "sports", "match ", " vs ", "tournament", "league",
    )):
        return "sporting_event", "Sports", None

    # ── Music ─────────────────────────────────────────────────────────────────
    if any(w in text for w in (
        "concert", "music festival", "music in ", "gig", "edm", "dj ",
        "live music", "band ", "electronic", "techno", "hip hop", "jazz",
        "classical music", "sufi", "folk music", "band", "singer",
        "bollywood night", "disco", "rave", "afterparty",
    )):
        return "music_festival", "Concert", None

    # ── Comedy ────────────────────────────────────────────────────────────────
    if any(w in text for w in (
        "comedy", "standup", "stand-up", "stand up", "comic", "open mic",
        "openmic", "open-mic", "roast", "improv", "jokes",
    )):
        return "comedy", "Comedy Show", None

    # ── Workshop / Class ──────────────────────────────────────────────────────
    if any(w in text for w in (
        "workshop", "masterclass", "master class", "bootcamp", "boot camp",
        "training", "certification", "course ", "class ", "learn ", "skill",
        "hackathon", "webinar",
    )):
        return "workshop", "Workshop", None

    # ── Theater / Performing Arts ─────────────────────────────────────────────
    if any(w in text for w in (
        "theatre", "theater", " play ", "drama", "musical ", "dance show",
        "ballet", "opera", "circus", "magic show", "puppet",
    )):
        return "entertainment", "Theater & Performing Arts", None

    # ── Exhibition / Expo ─────────────────────────────────────────────────────
    if any(w in text for w in (
        "exhibition", "expo ", "fair ", "art show", "gallery", "showcase",
        "trade show", "craft fair",
    )):
        return "entertainment", "Exhibition", None

    # ── Food & Drink ──────────────────────────────────────────────────────────
    if any(w in text for w in (
        "food festival", "food fest", "culinary", "wine tasting", "beer fest",
        "beer festival", "dining experience", "food walk",
    )):
        return "entertainment", "Food & Drink", None

    # ── Conference / Summit ───────────────────────────────────────────────────
    if any(w in text for w in (
        "conference", "summit", "meetup", "networking", "startup", "tech talk",
        "conclave", "symposium", "forum ", "seminar",
    )):
        return "conference", "Conference", None

    # Default
    return "conference", "Events", None

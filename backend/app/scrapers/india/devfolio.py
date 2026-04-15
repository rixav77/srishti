"""Devfolio scraper — India's largest hackathon platform.

Strategy:
  Phase 1 — GET https://devfolio.co/hackathons, parse __NEXT_DATA__ JSON
             embedded in the HTML to extract all hackathon slugs.
  Phase 2 — GET https://{slug}.devfolio.co for each slug, parse __NEXT_DATA__
             for full event data: prizes, sponsor tiers, judges.

No browser/JS needed — __NEXT_DATA__ is fully server-rendered.
"""
import asyncio
import logging
import re
import json

import httpx

from ..base import BaseScraper
from ..normalize import make_event, classify_event

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

LISTING_URLS = [
    "https://devfolio.co/hackathons",
]


# ── helpers ───────────────────────────────────────────────────────────────────

def _extract_next_data(html: str) -> dict | None:
    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html, re.DOTALL,
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _get_slugs_from_listing(html: str) -> list[str]:
    data = _extract_next_data(html)
    if not data:
        # Fallback: regex on raw HTML
        return list(set(re.findall(r'"slug":"([a-z0-9-]+)"', html)))
    try:
        queries = data["props"]["pageProps"]["dehydratedState"]["queries"]
        hackathons_data = queries[0]["state"]["data"]
        slugs = []
        for key in ("open_hackathons", "upcoming_hackathons", "featured_hackathons", "past_hackathons"):
            for h in hackathons_data.get(key, []):
                slug = h.get("slug")
                if slug:
                    slugs.append(slug)
        return list(dict.fromkeys(slugs))  # deduplicate preserving order
    except (KeyError, IndexError, TypeError):
        return list(set(re.findall(r'"slug":"([a-z0-9-]+)"', html)))


def _parse_event_page(html: str, slug: str) -> dict | None:
    data = _extract_next_data(html)
    if not data:
        return None
    try:
        props = data["props"]["pageProps"]
    except KeyError:
        return None

    h = props.get("hackathon") or {}
    if not h or not h.get("name"):
        return None

    # ── Basic fields ──────────────────────────────────────────────────────────
    name        = h.get("name", "").strip()
    tagline     = (h.get("tagline") or "").strip()
    description = (h.get("desc") or "").strip()
    starts_at   = (h.get("starts_at") or "").split("T")[0]
    ends_at     = (h.get("ends_at") or "").split("T")[0]
    city        = (h.get("city") or "").strip() or None
    location    = (h.get("location") or "").strip() or None
    is_online   = h.get("is_online", False)
    participants = h.get("participants_count") or 0

    # ── Prizes ────────────────────────────────────────────────────────────────
    prize_value    = props.get("aggregatePrizeValue")
    prize_currency = props.get("aggregatePrizeCurrency") or "USD"

    prize_min = prize_max = None
    if prize_value:
        try:
            prize_min = prize_max = float(prize_value)
        except (ValueError, TypeError):
            pass

    # Detailed prize breakdown per sponsor track
    prize_details = []
    for sponsor in props.get("prizeDetails") or []:
        sponsor_name = sponsor.get("name", "")
        for prize in sponsor.get("prizes") or []:
            amount   = prize.get("amount")
            currency = prize.get("currency") or prize_currency
            pname    = prize.get("name") or ""
            qty      = prize.get("quantity") or 1
            if amount:
                prize_details.append({
                    "sponsor": sponsor_name,
                    "prize":   pname,
                    "amount":  amount,
                    "currency": currency,
                    "quantity": qty,
                })

    # ── Sponsors ──────────────────────────────────────────────────────────────
    sponsors = []
    for tier in h.get("sponsor_tiers") or []:
        for sp in tier.get("sponsors") or []:
            sname = sp.get("name") or (sp.get("company") or {}).get("name")
            if sname and sname not in sponsors:
                sponsors.append(sname)

    # ── Judges / Speakers ─────────────────────────────────────────────────────
    judges = []
    for j in props.get("judges") or []:
        jname = (j.get("name") or "").strip()
        if jname:
            judges.append(jname)

    # ── Themes / Tracks ──────────────────────────────────────────────────────
    themes = [
        t.get("theme", {}).get("name", "")
        for t in h.get("themes") or []
        if t.get("theme", {}).get("name")
    ]

    return {
        "title":         name,
        "tagline":       tagline,
        "description":   (tagline + " " + description)[:800].strip() or None,
        "date":          starts_at,
        "end_date":      ends_at,
        "city":          city,
        "location":      location,
        "is_online":     is_online,
        "participants":  participants,
        "sponsors":      sponsors,
        "speakers":      judges,
        "prize_details": prize_details,
        "themes":        themes,
        "_prize_min":    prize_min,
        "_prize_max":    prize_max,
        "_prize_currency": prize_currency,
        "_slug":         slug,
    }


# ── scraper ───────────────────────────────────────────────────────────────────

class DevfolioScraper(BaseScraper):
    source_name    = "devfolio"
    max_concurrent = 5

    async def _fetch(self, client: httpx.AsyncClient, url: str) -> str | None:
        try:
            r = await client.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
            if r.status_code == 200:
                return r.text
            logger.debug(f"[devfolio] {url} → HTTP {r.status_code}")
            return None
        except Exception as exc:
            logger.warning(f"[devfolio] Fetch error {url}: {exc}")
            return None

    async def scrape(self, **kwargs) -> list[dict]:
        async with httpx.AsyncClient() as client:
            # Phase 1 — collect slugs from all listing pages
            slugs: list[str] = []
            for listing_url in LISTING_URLS:
                html = await self._fetch(client, listing_url)
                if html:
                    new_slugs = _get_slugs_from_listing(html)
                    logger.info(f"[devfolio] {listing_url} → {len(new_slugs)} slugs")
                    slugs.extend(new_slugs)

            # Deduplicate
            slugs = list(dict.fromkeys(slugs))
            logger.info(f"[devfolio] Total unique slugs: {len(slugs)}")

            if not slugs:
                return []

            # Phase 2 — fetch each hackathon subdomain concurrently in batches
            raw_events: list[dict] = []
            sem = asyncio.Semaphore(self.max_concurrent)

            async def fetch_event(slug: str) -> dict | None:
                async with sem:
                    url  = f"https://{slug}.devfolio.co"
                    html = await self._fetch(client, url)
                    if not html:
                        return None
                    raw = _parse_event_page(html, slug)
                    if raw:
                        raw["_source_url"] = url
                    return raw

            tasks   = [fetch_event(slug) for slug in slugs]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, dict) and r:
                    raw_events.append(r)

            return raw_events

    # ── normalise ─────────────────────────────────────────────────────────────

    def normalize(self, raw: dict) -> dict | None:
        name = (raw.get("title") or "").strip()
        if not name or len(name) < 3:
            return None

        from ..normalize import parse_date
        start_date = parse_date(raw.get("date") or "")
        end_date   = parse_date(raw.get("end_date") or "")

        city     = (raw.get("city") or "").strip() or None
        location = (raw.get("location") or "").strip() or None

        # Infer city from location string if not set
        if not city and location:
            parts = [p.strip() for p in location.split(",")]
            # Usually "Venue, Area, City, State, Country"
            if len(parts) >= 3:
                city = parts[-3]  # third from end is usually city

        country = "India" if not raw.get("is_online") else None

        prize_min = raw.get("_prize_min")
        prize_max = raw.get("_prize_max")
        currency  = raw.get("_prize_currency") or "USD"

        description = (raw.get("description") or "")[:500] or None
        sponsors    = raw.get("sponsors") or []
        speakers    = raw.get("speakers") or []

        domain, category_label, subcategory = classify_event(
            name=name,
            description=description or "",
            category=" ".join(raw.get("themes") or []),
            source_url=raw.get("_source_url", ""),
        )
        # Devfolio is always hackathon/workshop territory
        if domain not in ("workshop", "conference"):
            domain = "conference"
        category_label = "Hackathon"
        subcategory    = "Tech"

        return make_event(
            name=name,
            domain=domain,
            category=category_label,
            subcategory=subcategory,
            description=description,
            start_date=start_date,
            end_date=end_date,
            city=city,
            country=country,
            venue_name=location,
            estimated_attendance=raw.get("participants") or None,
            ticket_price_min=prize_min,
            ticket_price_max=prize_max,
            currency=currency,
            website_url=raw.get("_source_url"),
            sponsors=sponsors,
            speakers=speakers,
            data_source="devfolio",
            extraction_method="httpx_next_data",
            raw_data={k: v for k, v in raw.items() if not k.startswith("_")},
        )

"""Ticketmaster Discovery API v2 scraper.

Fetches events with price ranges across supported countries.
Requires TICKETMASTER_API_KEY in environment.

Supported countries (Ticketmaster coverage):
  US, CA, GB, IE, AU, NZ, MX, AT, BE, DE, DK, ES, FI, FR, NL, NO, PL, SE
Note: India (IN) is NOT supported by Ticketmaster.
"""
import asyncio
import logging
import os

import httpx

from ..base import BaseScraper
from ..normalize import make_event

logger = logging.getLogger(__name__)

TM_BASE = "https://app.ticketmaster.com/discovery/v2"

# Segments to fetch — maps to Ticketmaster classification names
SEGMENTS = ["Music", "Sports", "Arts & Theatre", "Family"]

# Countries to fetch — grouped by priority
COUNTRIES_PRIMARY = ["US", "GB", "CA", "AU", "DE", "FR"]
COUNTRIES_SECONDARY = ["IE", "NL", "BE", "SE", "NO", "DK", "AT", "ES", "PL", "MX", "NZ", "FI"]

START_DATE = "2025-01-01T00:00:00Z"
END_DATE   = "2026-12-31T23:59:59Z"

# Max events per segment × country slice (Ticketmaster caps at page*size < 1000)
PAGE_SIZE = 200
MAX_PAGES = 5   # 200 × 5 = 1000 events per segment-country pair (API hard cap)


class TicketmasterScraper(BaseScraper):
    source_name = "ticketmaster"

    async def scrape(self, **kwargs) -> list[dict]:
        api_key = os.environ.get("TICKETMASTER_API_KEY", "")
        if not api_key:
            logger.error("[ticketmaster] TICKETMASTER_API_KEY not set — skipping")
            return []

        raw_events: list[dict] = []
        countries = COUNTRIES_PRIMARY + COUNTRIES_SECONDARY

        async with httpx.AsyncClient(timeout=20) as client:
            for segment in SEGMENTS:
                for country in countries:
                    fetched = await self._fetch_segment_country(
                        client, api_key, segment, country
                    )
                    raw_events.extend(fetched)
                    logger.info(
                        f"[ticketmaster] {segment}/{country} → {len(fetched)} events"
                    )
                    # Respect rate limit: 5 req/s → small delay between batches
                    await asyncio.sleep(0.25)

        logger.info(f"[ticketmaster] Total raw events: {len(raw_events)}")
        return raw_events

    async def _fetch_segment_country(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        segment: str,
        country: str,
    ) -> list[dict]:
        events: list[dict] = []

        for page in range(MAX_PAGES):
            params = {
                "apikey": api_key,
                "classificationName": segment,
                "countryCode": country,
                "startDateTime": START_DATE,
                "endDateTime": END_DATE,
                "size": PAGE_SIZE,
                "page": page,
                "sort": "date,asc",
                # Only return events that have price info where possible
                # (no filter exists for this — we filter in normalize)
            }
            try:
                resp = await client.get(f"{TM_BASE}/events.json", params=params)
                if resp.status_code == 429:
                    logger.warning("[ticketmaster] Rate limited — sleeping 2s")
                    await asyncio.sleep(2)
                    resp = await client.get(f"{TM_BASE}/events.json", params=params)
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.warning(f"[ticketmaster] HTTP {e.response.status_code} for {segment}/{country} page {page}")
                break
            except httpx.RequestError as e:
                logger.warning(f"[ticketmaster] Request error: {e}")
                break

            data = resp.json()
            embedded = data.get("_embedded", {})
            batch = embedded.get("events", [])
            if not batch:
                break

            # Tag each event with scrape context
            for ev in batch:
                ev["_segment"] = segment
                ev["_country"] = country
            events.extend(batch)

            # Check if there are more pages
            page_meta = data.get("page", {})
            total_pages = page_meta.get("totalPages", 1)
            if page + 1 >= total_pages:
                break

        return events

    def normalize(self, raw: dict) -> dict | None:
        name = (raw.get("name") or "").strip()
        if not name:
            return None

        # Dates
        start_date = (
            raw.get("dates", {}).get("start", {}).get("localDate")
            or raw.get("dates", {}).get("start", {}).get("dateTime", "")[:10]
        )

        # Venue
        venues = raw.get("_embedded", {}).get("venues", [])
        venue = venues[0] if venues else {}
        venue_name = venue.get("name")
        city     = venue.get("city", {}).get("name")
        country  = venue.get("country", {}).get("name")
        address  = venue.get("address", {}).get("line1")

        # Price ranges — take the first range marked "standard" or just the first one
        price_ranges = raw.get("priceRanges", [])
        price_range = next(
            (p for p in price_ranges if p.get("type") == "standard"),
            price_ranges[0] if price_ranges else None,
        )
        ticket_price_min = price_range.get("min") if price_range else None
        ticket_price_max = price_range.get("max") if price_range else None
        currency = price_range.get("currency", "USD") if price_range else "USD"

        # Classification — segment → domain, genre → category
        classifications = raw.get("classifications", [])
        primary_class = next(
            (c for c in classifications if c.get("primary")),
            classifications[0] if classifications else {}
        )
        segment_name = primary_class.get("segment", {}).get("name", raw.get("_segment", ""))
        genre_name   = primary_class.get("genre", {}).get("name", "")
        subgenre     = primary_class.get("subGenre", {}).get("name", "")

        domain_map = {
            "Music": "music_festival",
            "Sports": "sporting_event",
            "Arts & Theatre": "conference",  # closest domain; covers theatre, comedy, arts
            "Family": "conference",
        }
        domain = domain_map.get(segment_name, "conference")
        category = genre_name or segment_name
        subcategory = subgenre or None

        return make_event(
            name=name,
            domain=domain,
            category=category,
            subcategory=subcategory,
            start_date=start_date,
            city=city,
            country=country,
            venue_name=venue_name,
            ticket_price_min=ticket_price_min,
            ticket_price_max=ticket_price_max,
            currency=currency,
            website_url=raw.get("url"),
            data_source="ticketmaster",
            extraction_method="ticketmaster_api_v2",
            raw_data={
                "id": raw.get("id"),
                "segment": segment_name,
                "genre": genre_name,
                "subgenre": subgenre,
                "address": address,
                "sales_start": raw.get("sales", {}).get("public", {}).get("startDateTime"),
                "country_code": raw.get("_country"),
            },
        )

"""Supabase database client — single connection module for all agents and routes.

Usage:
    from app.data.database import get_db, Database

    db = get_db()

    # Query events
    events = await db.get_events(domain="conference", city="Bengaluru", limit=20)

    # Vector-search-assisted: get events by IDs from Pinecone results
    events = await db.get_events_by_ids(["uuid1", "uuid2"])

    # Sponsors for an event
    sponsors = await db.get_event_sponsors(event_id)

    # Full-text / filter search
    results = await db.search_events(query="AI hackathon", domain="conference")
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from supabase import create_client, Client

from app.config import get_settings

logger = logging.getLogger(__name__)


# ── singleton client ───────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set in .env"
        )
    return create_client(settings.supabase_url, settings.supabase_key)


# ── database facade ────────────────────────────────────────────────────────────

class Database:
    """Thin wrapper around the Supabase client with typed helper methods."""

    def __init__(self) -> None:
        self._sb = _get_client()

    # ── events ─────────────────────────────────────────────────────────────────

    def get_events(
        self,
        *,
        domain: str | None = None,
        category: str | None = None,
        city: str | None = None,
        country: str | None = None,
        year: int | None = None,
        data_source: str | None = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "start_date",
    ) -> list[dict]:
        """Fetch events with optional filters. Returns list of event dicts."""
        q = self._sb.table("events").select(
            "id, name, domain, category, subcategory, description, "
            "start_date, end_date, city, country, venue_name, "
            "estimated_attendance, ticket_price_min, ticket_price_max, "
            "currency, website_url, year, data_source, extraction_method"
        )

        if domain:
            q = q.eq("domain", domain)
        if category:
            q = q.ilike("category", f"%{category}%")
        if city:
            q = q.ilike("city", f"%{city}%")
        if country:
            q = q.ilike("country", f"%{country}%")
        if year:
            q = q.eq("year", year)
        if data_source:
            q = q.eq("data_source", data_source)

        q = q.order(order_by).range(offset, offset + limit - 1)
        resp = q.execute()
        return resp.data or []

    def get_event_by_id(self, event_id: str) -> dict | None:
        """Fetch a single event by UUID, including raw_data and enrichment."""
        resp = (
            self._sb.table("events")
            .select("*")
            .eq("id", event_id)
            .single()
            .execute()
        )
        return resp.data

    def get_events_by_ids(self, event_ids: list[str]) -> list[dict]:
        """Fetch multiple events by UUID list (used after Pinecone vector search)."""
        if not event_ids:
            return []
        resp = (
            self._sb.table("events")
            .select("*")
            .in_("id", event_ids)
            .execute()
        )
        return resp.data or []

    def count_events(
        self,
        domain: str | None = None,
        year: int | None = None,
    ) -> int:
        q = self._sb.table("events").select("id", count="exact")
        if domain:
            q = q.eq("domain", domain)
        if year:
            q = q.eq("year", year)
        resp = q.execute()
        return resp.count or 0

    # ── sponsors ───────────────────────────────────────────────────────────────

    def get_event_sponsors(self, event_id: str) -> list[dict]:
        """Return sponsors for a given event (with tier info)."""
        resp = (
            self._sb.table("event_sponsors")
            .select("tier, estimated_amount, currency, sponsors(id, company_name, industry, website_url)")
            .eq("event_id", event_id)
            .execute()
        )
        rows = resp.data or []
        result = []
        for row in rows:
            sponsor = row.get("sponsors") or {}
            result.append({
                "id":             sponsor.get("id"),
                "company_name":   sponsor.get("company_name"),
                "industry":       sponsor.get("industry"),
                "website_url":    sponsor.get("website_url"),
                "tier":           row.get("tier"),
                "estimated_amount": row.get("estimated_amount"),
                "currency":       row.get("currency"),
            })
        return result

    def get_sponsors(
        self,
        *,
        industry: str | None = None,
        country: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        q = self._sb.table("sponsors").select("*")
        if industry:
            q = q.ilike("industry", f"%{industry}%")
        if country:
            q = q.ilike("headquarters_country", f"%{country}%")
        q = q.limit(limit)
        return q.execute().data or []

    # ── talents ────────────────────────────────────────────────────────────────

    def get_event_talents(self, event_id: str) -> list[dict]:
        """Return speakers/artists/athletes for a given event."""
        resp = (
            self._sb.table("event_talents")
            .select("role, session_title, talents(id, name, type, title, organization, topics)")
            .eq("event_id", event_id)
            .execute()
        )
        rows = resp.data or []
        result = []
        for row in rows:
            talent = row.get("talents") or {}
            result.append({
                "id":            talent.get("id"),
                "name":          talent.get("name"),
                "type":          talent.get("type"),
                "title":         talent.get("title"),
                "organization":  talent.get("organization"),
                "topics":        talent.get("topics") or [],
                "role":          row.get("role"),
                "session_title": row.get("session_title"),
            })
        return result

    def get_talents(
        self,
        *,
        talent_type: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        q = self._sb.table("talents").select("*")
        if talent_type:
            q = q.eq("type", talent_type)
        q = q.limit(limit)
        return q.execute().data or []

    # ── venues ─────────────────────────────────────────────────────────────────

    def get_venues(
        self,
        *,
        city: str | None = None,
        country: str | None = None,
        min_capacity: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        q = self._sb.table("venues").select("*")
        if city:
            q = q.ilike("city", f"%{city}%")
        if country:
            q = q.ilike("country", f"%{country}%")
        if min_capacity:
            q = q.gte("max_capacity", min_capacity)
        q = q.limit(limit)
        return q.execute().data or []

    # ── stats ──────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Summary counts across all tables — used by /api/datasets/stats."""
        def count(table: str, filters: dict | None = None) -> int:
            q = self._sb.table(table).select("id", count="exact")
            if filters:
                for col, val in filters.items():
                    q = q.eq(col, val)
            return q.execute().count or 0

        total_events    = count("events")
        conferences     = count("events", {"domain": "conference"})
        music           = count("events", {"domain": "music_festival"})
        sports          = count("events", {"domain": "sporting_event"})
        total_sponsors  = count("sponsors")
        total_talents   = count("talents")
        total_venues    = count("venues")

        # Year breakdown
        events_2025 = count("events")  # rough — filter below
        resp_2025 = (
            self._sb.table("events")
            .select("id", count="exact")
            .eq("year", 2025)
            .execute()
        )
        resp_2026 = (
            self._sb.table("events")
            .select("id", count="exact")
            .eq("year", 2026)
            .execute()
        )

        # City/country diversity
        city_resp = (
            self._sb.table("events")
            .select("city")
            .not_.is_("city", "null")
            .execute()
        )
        country_resp = (
            self._sb.table("events")
            .select("country")
            .not_.is_("country", "null")
            .execute()
        )
        unique_cities    = len({r["city"]    for r in (city_resp.data    or [])})
        unique_countries = len({r["country"] for r in (country_resp.data or [])})

        return {
            "events": {
                "total":          total_events,
                "by_domain": {
                    "conference":     conferences,
                    "music_festival": music,
                    "sporting_event": sports,
                },
                "by_year": {
                    "2025": resp_2025.count or 0,
                    "2026": resp_2026.count or 0,
                },
                "unique_cities":    unique_cities,
                "unique_countries": unique_countries,
            },
            "sponsors":   {"total": total_sponsors},
            "talents":    {"total": total_talents},
            "venues":     {"total": total_venues},
        }

    # ── search ─────────────────────────────────────────────────────────────────

    def search_events(
        self,
        *,
        query: str,
        domain: str | None = None,
        city: str | None = None,
        country: str | None = None,
        year: int | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """
        Keyword search across name + description + category.
        For semantic search, use the Pinecone vector search then call
        get_events_by_ids() with the returned UUIDs.
        """
        q = (
            self._sb.table("events")
            .select(
                "id, name, domain, category, description, start_date, "
                "city, country, venue_name, ticket_price_min, ticket_price_max, "
                "currency, website_url, estimated_attendance"
            )
            .or_(
                f"name.ilike.%{query}%,"
                f"description.ilike.%{query}%,"
                f"category.ilike.%{query}%,"
                f"venue_name.ilike.%{query}%"
            )
        )

        if domain:
            q = q.eq("domain", domain)
        if city:
            q = q.ilike("city", f"%{city}%")
        if country:
            q = q.ilike("country", f"%{country}%")
        if year:
            q = q.eq("year", year)

        q = q.order("start_date").limit(limit)
        return q.execute().data or []


# ── module-level singleton ─────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_db() -> Database:
    """Return the shared Database instance (created once per process)."""
    return Database()

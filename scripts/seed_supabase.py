"""Upload enriched event data to Supabase (PostgreSQL).

Usage:
    cd /home/yash/srishti
    source venv/bin/activate
    python scripts/seed_supabase.py

Requires .env with:
    SUPABASE_URL=https://xxxx.supabase.co
    SUPABASE_KEY=<service_role key>   ← use the service_role key, NOT the anon key

What this does:
  1. Reads data/conferences_2025_2026.json
             data/music_festivals_2025_2026.json
             data/sporting_events_2025_2026.json
  2. Upserts all 241 events into the `events` table
     (conflict on name + start_date + city → update)
  3. Upserts deduplicated sponsors into `sponsors`
  4. Upserts deduplicated talents  into `talents`
  5. Upserts junction rows into `event_sponsors` and `event_talents`
  6. Infers venue rows from venue_name + city and upserts into `venues`

All operations are idempotent — safe to re-run.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# ── config ────────────────────────────────────────────────────────────────────

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")   # must be service_role key

if not SUPABASE_URL or not SUPABASE_KEY:
    sys.exit("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

DATA_FILES = [
    DATA_DIR / "conferences_2025_2026.json",
    DATA_DIR / "music_festivals_2025_2026.json",
    DATA_DIR / "sporting_events_2025_2026.json",
]

# Infer talent type from domain (will be refined later)
DOMAIN_TALENT_TYPE = {
    "conference":     "speaker",
    "music_festival": "artist",
    "sporting_event": "athlete",
}

DOMAIN_TALENT_ROLE = {
    "conference":     "speaker",
    "music_festival": "headliner",
    "sporting_event": "athlete",
}


# ── helpers ───────────────────────────────────────────────────────────────────

def load_events() -> list[dict]:
    events = []
    for path in DATA_FILES:
        if not path.exists():
            print(f"  WARNING: {path} not found, skipping")
            continue
        with open(path) as f:
            batch = json.load(f)
        print(f"  Loaded {len(batch):>4} events from {path.name}")
        events.extend(batch)
    return events


def build_event_row(e: dict) -> dict:
    """Map JSON event fields → events table columns."""
    return {
        "name":                 e["name"],
        "domain":               e["domain"],
        "category":             e.get("category"),
        "subcategory":          e.get("subcategory"),
        "description":          (e.get("description") or "")[:2000] or None,
        "start_date":           e.get("start_date"),
        "end_date":             e.get("end_date"),
        "city":                 e.get("city"),
        "country":              e.get("country"),
        "continent":            _infer_continent(e.get("country")),
        "venue_name":           e.get("venue_name"),
        "estimated_attendance": e.get("estimated_attendance"),
        "ticket_price_min":     e.get("ticket_price_min"),
        "ticket_price_max":     e.get("ticket_price_max"),
        "currency":             e.get("currency", "USD"),
        "website_url":          e.get("website_url"),
        "data_source":          e.get("data_source"),
        "extraction_method":    e.get("extraction_method"),
        "raw_data":             e.get("raw_data", {}),
        "enrichment":           e.get("enrichment", {}),
    }


def _infer_continent(country: str | None) -> str | None:
    if not country:
        return None
    c = country.lower()
    if c in ("india", "pakistan", "bangladesh", "sri lanka", "nepal"):
        return "Asia"
    if c in ("usa", "united states", "canada", "mexico"):
        return "North America"
    if c in ("uk", "united kingdom", "germany", "france", "spain", "italy",
             "netherlands", "switzerland", "sweden", "norway", "denmark"):
        return "Europe"
    if c in ("australia", "new zealand"):
        return "Oceania"
    if c in ("brazil", "argentina", "colombia", "chile"):
        return "South America"
    if c in ("nigeria", "kenya", "south africa", "ghana"):
        return "Africa"
    return None


# ── upsert helpers ─────────────────────────────────────────────────────────────

def upsert_batch(sb: Client, table: str, rows: list[dict],
                 on_conflict: str, batch_size: int = 100) -> int:
    """Upsert rows in batches. Returns total rows upserted."""
    total = 0
    for i in range(0, len(rows), batch_size):
        chunk = rows[i: i + batch_size]
        sb.table(table).upsert(chunk, on_conflict=on_conflict).execute()
        total += len(chunk)
    return total


# ── main pipeline ──────────────────────────────────────────────────────────────

def main():
    sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"\nConnected to Supabase: {SUPABASE_URL}\n")

    # ── 1. Load all events ────────────────────────────────────────────────────
    print("Loading event data...")
    events = load_events()
    print(f"  Total: {len(events)} events\n")

    # ── 2. Upsert events ─────────────────────────────────────────────────────
    print("Upserting events...")
    event_rows = [build_event_row(e) for e in events]
    n = upsert_batch(sb, "events", event_rows, on_conflict="name,start_date,city")
    print(f"  Upserted {n} event rows\n")

    # Fetch back inserted events to get their UUIDs for junction tables
    print("Fetching event UUIDs...")
    response = sb.table("events").select("id,name,start_date,city,domain").execute()
    event_lookup: dict[tuple, str] = {}   # (name, start_date, city) → id
    for row in response.data:
        key = (row["name"], row.get("start_date", ""), row.get("city", ""))
        event_lookup[key] = row["id"]
    print(f"  Got {len(event_lookup)} event UUIDs\n")

    # ── 3. Collect + upsert sponsors ──────────────────────────────────────────
    print("Building sponsors...")
    unique_sponsors: dict[str, dict] = {}   # name → row
    for e in events:
        for s in e.get("sponsors") or []:
            name = s.strip()
            if name and name not in unique_sponsors:
                unique_sponsors[name] = {
                    "company_name": name,
                    "data_source":  e.get("data_source"),
                }

    if unique_sponsors:
        n = upsert_batch(sb, "sponsors", list(unique_sponsors.values()),
                         on_conflict="company_name")
        print(f"  Upserted {n} sponsor rows")

    # Fetch sponsor UUIDs
    sponsor_resp = sb.table("sponsors").select("id,company_name").execute()
    sponsor_lookup: dict[str, str] = {r["company_name"]: r["id"] for r in sponsor_resp.data}
    print(f"  Got {len(sponsor_lookup)} sponsor UUIDs\n")

    # ── 4. Collect + upsert talents ───────────────────────────────────────────
    print("Building talents...")
    unique_talents: dict[str, dict] = {}   # name → row
    for e in events:
        ttype = DOMAIN_TALENT_TYPE.get(e["domain"], "speaker")
        for t in e.get("speakers") or []:
            name = t.strip()
            if name and name not in unique_talents:
                unique_talents[name] = {
                    "name":        name,
                    "type":        ttype,
                    "data_source": e.get("data_source"),
                }

    if unique_talents:
        n = upsert_batch(sb, "talents", list(unique_talents.values()),
                         on_conflict="name")
        print(f"  Upserted {n} talent rows")

    # Fetch talent UUIDs
    talent_resp = sb.table("talents").select("id,name").execute()
    talent_lookup: dict[str, str] = {r["name"]: r["id"] for r in talent_resp.data}
    print(f"  Got {len(talent_lookup)} talent UUIDs\n")

    # ── 5. Build junction rows ────────────────────────────────────────────────
    print("Building junction rows...")
    event_sponsor_rows = []
    event_talent_rows  = []

    for e in events:
        ekey = (e["name"], e.get("start_date", ""), e.get("city", ""))
        event_id = event_lookup.get(ekey)
        if not event_id:
            print(f"  WARNING: no UUID for event '{e['name']}' — skipping junctions")
            continue

        role = DOMAIN_TALENT_ROLE.get(e["domain"], "speaker")

        for s in e.get("sponsors") or []:
            name = s.strip()
            sid  = sponsor_lookup.get(name)
            if sid:
                event_sponsor_rows.append({
                    "event_id":   event_id,
                    "sponsor_id": sid,
                    "tier":       None,
                })

        for t in e.get("speakers") or []:
            name = t.strip()
            tid  = talent_lookup.get(name)
            if tid:
                event_talent_rows.append({
                    "event_id":  event_id,
                    "talent_id": tid,
                    "role":      role,
                })

    if event_sponsor_rows:
        n = upsert_batch(sb, "event_sponsors", event_sponsor_rows,
                         on_conflict="event_id,sponsor_id")
        print(f"  Upserted {n} event_sponsor rows")

    if event_talent_rows:
        n = upsert_batch(sb, "event_talents", event_talent_rows,
                         on_conflict="event_id,talent_id")
        print(f"  Upserted {n} event_talent rows")
    print()

    # ── 6. Infer + upsert venues ──────────────────────────────────────────────
    print("Building venues...")
    unique_venues: dict[tuple, dict] = {}   # (name, city) → row
    for e in events:
        vname = (e.get("venue_name") or "").strip()
        city  = (e.get("city") or "").strip()
        if not vname or not city:
            continue
        key = (vname, city)
        if key not in unique_venues:
            unique_venues[key] = {
                "name":        vname,
                "city":        city,
                "country":     e.get("country"),
                "data_source": e.get("data_source"),
            }

    if unique_venues:
        n = upsert_batch(sb, "venues", list(unique_venues.values()),
                         on_conflict="name,city")
        print(f"  Upserted {n} venue rows")
    print()

    # ── 7. Summary ────────────────────────────────────────────────────────────
    print("=" * 50)
    print("Seed complete!")
    resp = sb.table("events").select("domain", count="exact").execute()
    total = len(resp.data)
    by_domain = {}
    for row in resp.data:
        d = row["domain"]
        by_domain[d] = by_domain.get(d, 0) + 1
    print(f"  events total:          {total}")
    for d, cnt in sorted(by_domain.items()):
        print(f"    {d:<25} {cnt}")
    print(f"  sponsors:              {len(sponsor_lookup)}")
    print(f"  talents:               {len(talent_lookup)}")
    print(f"  event_sponsor links:   {len(event_sponsor_rows)}")
    print(f"  event_talent links:    {len(event_talent_rows)}")
    print(f"  venues:                {len(unique_venues)}")
    print("=" * 50)


if __name__ == "__main__":
    main()

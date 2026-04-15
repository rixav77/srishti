"""ETL pipeline — runs District, Mepass, and Skillboxes scrapers, deduplicates, validates, exports CSV + JSON."""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .normalize import dedup, is_valid
from .india.devfolio import DevfolioScraper
from .india.district import DistrictScraper
from .india.mepass import MepassScraper
from .india.skillboxes import SkillboxesScraper

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[4] / "srishti" / "data"

EXPORT_COLUMNS = [
    "name", "domain", "category", "subcategory", "description",
    "start_date", "end_date", "city", "country", "venue_name",
    "estimated_attendance", "ticket_price_min", "ticket_price_max", "currency",
    "website_url", "year", "sponsors", "speakers",
    "data_source", "extraction_method",
]


async def run_scrapers(scrapers: list) -> list[dict]:
    """Run scrapers concurrently and merge results."""
    tasks = [s.run() for s in scrapers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    merged = []
    for scraper, result in zip(scrapers, results):
        if isinstance(result, Exception):
            logger.error(f"[{scraper.source_name}] Failed: {result}")
        else:
            merged.extend(result)
    return merged


def export(events: list[dict], domain: str, data_dir: Path = DATA_DIR) -> tuple[Path, Path]:
    """Export events to CSV + JSON. Returns (csv_path, json_path)."""
    data_dir.mkdir(parents=True, exist_ok=True)
    slug = domain

    csv_path  = data_dir / f"{slug}s_2025_2026.csv"
    json_path = data_dir / f"{slug}s_2025_2026.json"

    flat = []
    for e in events:
        row = {k: e.get(k) for k in EXPORT_COLUMNS}
        row["sponsors"] = ", ".join(e.get("sponsors") or [])
        row["speakers"] = ", ".join(e.get("speakers") or [])
        flat.append(row)

    df = pd.DataFrame(flat, columns=EXPORT_COLUMNS)
    df.to_csv(csv_path, index=False)
    logger.info(f"Exported {len(df)} rows → {csv_path}")

    with open(json_path, "w") as f:
        json.dump(events, f, indent=2, default=str)
    logger.info(f"Exported {len(events)} records → {json_path}")

    return csv_path, json_path


# ── full pipeline ─────────────────────────────────────────────────────────────

async def run_full_pipeline() -> dict:
    """Run all scrapers and export datasets. Returns summary."""
    logger.info("=== Starting scraping pipeline (Devfolio + District + Mepass + Skillboxes) ===")

    scrapers = [
        DevfolioScraper(),
        DistrictScraper(),
        MepassScraper(),
        SkillboxesScraper(),
    ]

    all_events = await run_scrapers(scrapers)
    all_events = [e for e in all_events if is_valid(e)]
    all_events = dedup(all_events)
    logger.info(f"Total events after dedup: {len(all_events)}")

    # Split by domain for export
    conferences   = [e for e in all_events if e.get("domain") == "conference"]
    music         = [e for e in all_events if e.get("domain") == "music_festival"]
    sports        = [e for e in all_events if e.get("domain") == "sporting_event"]

    export(conferences, "conference")
    export(music,       "music_festival")
    export(sports,      "sporting_event")

    summary = {
        "conferences":    len(conferences),
        "music_festivals": len(music),
        "sporting_events": len(sports),
        "total":          len(all_events),
        "exported_at":    datetime.now(timezone.utc).isoformat(),
    }
    logger.info(f"Pipeline complete: {summary}")
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    asyncio.run(run_full_pipeline())

"""ETL pipeline — runs all scrapers, deduplicates, validates, exports CSV + JSON."""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .normalize import dedup, is_valid
from .conferences.conf_tech import ConfTechScraper
from .conferences.ten_times import TenTimesScraper
from .conferences.luma import LumaScraper
from .conferences.dev_events import DevEventsScraper
from .music.songkick import SongkickScraper
from .music.jambase import JamBaseScraper
from .sports.espn import ESPNScraper

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[4] / "data"

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
    slug = domain.replace("_", "_")  # music_festival, conference, sporting_event
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")

    csv_path = data_dir / f"{slug}s_2025_2026.csv"
    json_path = data_dir / f"{slug}s_2025_2026.json"

    # Flatten list fields for CSV
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


async def collect_conferences() -> list[dict]:
    scrapers = [
        ConfTechScraper(),
        TenTimesScraper(),
        LumaScraper(),
        DevEventsScraper(),
    ]
    events = await run_scrapers(scrapers)
    events = [e for e in events if is_valid(e)]
    events = dedup(events)
    logger.info(f"Conferences total after dedup: {len(events)}")
    return events


async def collect_music_festivals() -> list[dict]:
    scrapers = [SongkickScraper(), JamBaseScraper()]
    events = await run_scrapers(scrapers)
    events = [e for e in events if is_valid(e)]
    events = dedup(events)
    logger.info(f"Music festivals total after dedup: {len(events)}")
    return events


async def collect_sporting_events() -> list[dict]:
    scrapers = [ESPNScraper()]
    events = await run_scrapers(scrapers)
    events = [e for e in events if is_valid(e)]
    events = dedup(events)
    logger.info(f"Sporting events total after dedup: {len(events)}")
    return events


async def run_full_pipeline() -> dict:
    """Run all scrapers and export all datasets. Returns summary."""
    logger.info("=== Starting full scraping pipeline ===")

    conferences, festivals, sports = await asyncio.gather(
        collect_conferences(),
        collect_music_festivals(),
        collect_sporting_events(),
    )

    export(conferences, "conference")
    export(festivals, "music_festival")
    export(sports, "sporting_event")

    summary = {
        "conferences": len(conferences),
        "music_festivals": len(festivals),
        "sporting_events": len(sports),
        "total": len(conferences) + len(festivals) + len(sports),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(f"Pipeline complete: {summary}")
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    asyncio.run(run_full_pipeline())

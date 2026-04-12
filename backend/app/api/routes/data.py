from fastapi import APIRouter, BackgroundTasks, Query
from pathlib import Path
import json
import logging

from app.scrapers.pipeline import run_full_pipeline, collect_conferences, collect_music_festivals, collect_sporting_events
from app.scrapers.pipeline import export

logger = logging.getLogger(__name__)
router = APIRouter()

DATA_DIR = Path(__file__).resolve().parents[4] / "data"


@router.get("/events")
async def list_events(
    domain: str | None = None,
    year: int | None = None,
    category: str | None = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
):
    # Load from JSON files
    events = []
    for json_file in DATA_DIR.glob("*_2025_2026.json"):
        if domain and domain not in json_file.stem:
            continue
        if json_file.exists():
            with open(json_file) as f:
                file_events = json.load(f)
                events.extend(file_events)

    # Filter
    if year:
        events = [e for e in events if e.get("year") == year]
    if category:
        events = [
            e
            for e in events
            if category.lower() in (e.get("category", "") or "").lower()
        ]

    total = len(events)
    events = events[offset : offset + limit]

    return {"total": total, "events": events, "limit": limit, "offset": offset}


@router.get("/export")
async def export_dataset(domain: str = "conferences", format: str = "json"):
    filename = f"{domain}_2025_2026.{format}"
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return {"error": f"Dataset {filename} not found"}

    if format == "json":
        with open(filepath) as f:
            return json.load(f)
    return {"message": f"Download {filename}", "path": str(filepath)}


@router.post("/scrape")
async def trigger_scrape(
    domain: str | None = Query(default=None, description="conferences | music_festivals | sporting_events | all"),
    background_tasks: BackgroundTasks = None,
):
    """Trigger scraping pipeline. Runs in background and exports data files."""
    async def _run(domain: str | None):
        try:
            if domain == "conferences":
                events = await collect_conferences()
                export(events, "conference")
            elif domain == "music_festivals":
                events = await collect_music_festivals()
                export(events, "music_festival")
            elif domain == "sporting_events":
                events = await collect_sporting_events()
                export(events, "sporting_event")
            else:
                await run_full_pipeline()
        except Exception as e:
            logger.error(f"Scrape pipeline error: {e}", exc_info=True)

    if background_tasks:
        background_tasks.add_task(_run, domain)
        return {"status": "started", "domain": domain or "all", "message": "Scraping in background — check /datasets/events when done"}

    # Foreground for small domains
    await _run(domain)
    return {"status": "complete", "domain": domain or "all"}


@router.get("/stats")
async def dataset_stats():
    """Return count stats for all loaded datasets."""
    stats = {}
    for json_file in DATA_DIR.glob("*_2025_2026.json"):
        if json_file.exists():
            with open(json_file) as f:
                data = json.load(f)
            stats[json_file.stem] = len(data)
    stats["total"] = sum(stats.values())
    return stats

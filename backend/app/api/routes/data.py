from fastapi import APIRouter, Query
from pathlib import Path
import json

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

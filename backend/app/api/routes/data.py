"""Dataset routes — /api/datasets/*

Endpoints:
  GET  /api/datasets/stats              — counts across all tables
  GET  /api/datasets/events             — paginated event list with filters
  GET  /api/datasets/events/{id}        — single event with sponsors + talents
  GET  /api/datasets/search             — keyword search across events
  GET  /api/datasets/sponsors           — sponsor list
  GET  /api/datasets/talents            — talent list
  GET  /api/datasets/venues             — venue list
  POST /api/datasets/scrape             — trigger scrape pipeline (background)
"""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.data.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ── stats ──────────────────────────────────────────────────────────────────────

@router.get("/stats")
def dataset_stats():
    """
    Summary counts: total events by domain, year, unique cities/countries,
    plus sponsor, talent, and venue counts.
    """
    try:
        return get_db().get_stats()
    except Exception as exc:
        logger.error(f"Stats error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ── events ─────────────────────────────────────────────────────────────────────

@router.get("/events")
def list_events(
    domain:      Annotated[str | None, Query(description="conference | music_festival | sporting_event")] = None,
    category:    Annotated[str | None, Query()] = None,
    city:        Annotated[str | None, Query()] = None,
    country:     Annotated[str | None, Query()] = None,
    year:        Annotated[int | None, Query()] = None,
    data_source: Annotated[str | None, Query()] = None,
    limit:       Annotated[int, Query(ge=1, le=500)] = 50,
    offset:      Annotated[int, Query(ge=0)] = 0,
):
    """Paginated event listing with optional filters."""
    try:
        db = get_db()
        events = db.get_events(
            domain=domain,
            category=category,
            city=city,
            country=country,
            year=year,
            data_source=data_source,
            limit=limit,
            offset=offset,
        )
        total = db.count_events(domain=domain, year=year)
        return {
            "total":  total,
            "limit":  limit,
            "offset": offset,
            "events": events,
        }
    except Exception as exc:
        logger.error(f"List events error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/events/{event_id}")
def get_event(event_id: str):
    """
    Full event detail — includes sponsors and speakers/artists/athletes
    from the junction tables.
    """
    try:
        db    = get_db()
        event = db.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        sponsors = db.get_event_sponsors(event_id)
        talents  = db.get_event_talents(event_id)

        return {
            **event,
            "sponsors": sponsors,
            "talents":  talents,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Get event error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ── search ─────────────────────────────────────────────────────────────────────

@router.get("/search")
def search_events(
    q:       Annotated[str, Query(min_length=2, description="Search term")],
    domain:  Annotated[str | None, Query()] = None,
    city:    Annotated[str | None, Query()] = None,
    country: Annotated[str | None, Query()] = None,
    year:    Annotated[int | None, Query()] = None,
    limit:   Annotated[int, Query(ge=1, le=100)] = 20,
):
    """
    Keyword search across event name, description, category, and venue.
    For semantic/vector search the agents use Pinecone directly and then
    call get_events_by_ids() — this endpoint is for simple text queries.
    """
    try:
        results = get_db().search_events(
            query=q,
            domain=domain,
            city=city,
            country=country,
            year=year,
            limit=limit,
        )
        return {
            "query":   q,
            "total":   len(results),
            "results": results,
        }
    except Exception as exc:
        logger.error(f"Search error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ── sponsors ───────────────────────────────────────────────────────────────────

@router.get("/sponsors")
def list_sponsors(
    industry: Annotated[str | None, Query()] = None,
    country:  Annotated[str | None, Query()] = None,
    limit:    Annotated[int, Query(ge=1, le=200)] = 50,
):
    try:
        return get_db().get_sponsors(industry=industry, country=country, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── talents ────────────────────────────────────────────────────────────────────

@router.get("/talents")
def list_talents(
    type:  Annotated[str | None, Query(description="speaker | artist | athlete | judge")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    try:
        return get_db().get_talents(talent_type=type, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── venues ─────────────────────────────────────────────────────────────────────

@router.get("/venues")
def list_venues(
    city:         Annotated[str | None, Query()] = None,
    country:      Annotated[str | None, Query()] = None,
    min_capacity: Annotated[int | None, Query()] = None,
    limit:        Annotated[int, Query(ge=1, le=200)] = 50,
):
    try:
        return get_db().get_venues(
            city=city,
            country=country,
            min_capacity=min_capacity,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── scrape trigger (kept from original) ───────────────────────────────────────

@router.post("/scrape")
async def trigger_scrape(
    domain: Annotated[str | None, Query(description="conferences | music_festivals | sporting_events | all")] = None,
    background_tasks: BackgroundTasks = None,
):
    """Trigger the scraping pipeline in the background."""
    from app.scrapers.pipeline import run_full_pipeline

    async def _run():
        try:
            await run_full_pipeline()
        except Exception as exc:
            logger.error(f"Scrape pipeline error: {exc}", exc_info=True)

    if background_tasks:
        background_tasks.add_task(_run)
        return {
            "status":  "started",
            "domain":  domain or "all",
            "message": "Scraping in background",
        }

    await _run()
    return {"status": "complete", "domain": domain or "all"}

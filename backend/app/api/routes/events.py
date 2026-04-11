from fastapi import APIRouter, HTTPException
from uuid import uuid4

from app.data.models import EventConfig, EventPlanResponse, EventStatus

router = APIRouter()

# In-memory store for hackathon (replace with DB later)
_event_plans: dict[str, dict] = {}


@router.post("/configure", response_model=EventPlanResponse)
async def configure_event(config: EventConfig):
    event_id = str(uuid4())
    _event_plans[event_id] = {
        "id": event_id,
        "config": config.model_dump(),
        "status": "processing",
        "completed_agents": [],
        "results": {},
    }

    # TODO: Trigger orchestrator in background
    # asyncio.create_task(run_orchestrator(event_id, config))

    return EventPlanResponse(
        event_id=event_id,
        status="processing",
        message="Agents are working on your event plan...",
    )


@router.get("/{event_id}/status", response_model=EventStatus)
async def get_event_status(event_id: str):
    plan = _event_plans.get(event_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventStatus(
        event_id=event_id,
        status=plan["status"],
        completed_agents=plan["completed_agents"],
        total_agents=7,
    )


@router.get("/{event_id}/plan")
async def get_event_plan(event_id: str):
    plan = _event_plans.get(event_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Event not found")
    return plan

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from uuid import uuid4

from app.agents.orchestrator import Orchestrator
from app.api.websocket import broadcast_event
from app.data.models import EventConfig, EventPlanResponse, EventStatus

router = APIRouter()

# In-memory store for hackathon (replace with DB later)
_event_plans: dict[str, dict] = {}
_running_tasks: dict[str, asyncio.Task] = {}
_orchestrator = Orchestrator()


async def _run_orchestrator(event_id: str, config: EventConfig) -> None:
    """Run orchestrator in background and continuously update the in-memory plan."""
    plan = _event_plans.get(event_id)
    if not plan:
        return

    try:
        await broadcast_event(event_id, {"type": "plan_started", "event_id": event_id})

        async for update in _orchestrator.run_stream(config):
            agent_name = update.get("agent")
            status = update.get("status")

            if agent_name == "orchestrator" and status == "complete":
                # Final consolidated plan from orchestrator
                final_plan = update.get("plan", {})
                terminal_status = "completed" if not plan["failed_agents"] else "partial_failed"
                plan["status"] = terminal_status
                plan["consolidated_plan"] = final_plan
                plan["completed_at"] = datetime.now(timezone.utc).isoformat()
                await broadcast_event(
                    event_id,
                    {
                        "type": "plan_completed" if terminal_status == "completed" else "plan_partial_failed",
                        "event_id": event_id,
                        "status": terminal_status,
                        "plan": final_plan,
                    },
                )
                continue

            # Per-agent updates
            if agent_name and agent_name != "orchestrator":
                plan["results_by_agent"][agent_name] = update.get("results", {})
                plan["results"][agent_name] = update.get("results", {})
                if status == "completed" and agent_name not in plan["completed_agents"]:
                    plan["completed_agents"].append(agent_name)
                if status == "error" and agent_name not in plan["failed_agents"]:
                    plan["failed_agents"].append(agent_name)

            await broadcast_event(
                event_id,
                {
                    "type": "agent_update",
                    "event_id": event_id,
                    **update,
                },
            )

        if plan["status"] != "completed":
            plan["status"] = "completed" if not plan["failed_agents"] else "partial_failed"
            plan["completed_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as exc:
        plan["status"] = "failed"
        plan.setdefault("errors", []).append(str(exc))
        await broadcast_event(
            event_id,
            {
                "type": "plan_failed",
                "event_id": event_id,
                "error": str(exc),
            },
        )
    finally:
        _running_tasks.pop(event_id, None)


@router.post("/configure", response_model=EventPlanResponse)
async def configure_event(config: EventConfig):
    event_id = str(uuid4())
    _event_plans[event_id] = {
        "id": event_id,
        "config": config.model_dump(),
        "status": "processing",
        "completed_agents": [],
        "failed_agents": [],
        "results": {},
        "results_by_agent": {},
        "consolidated_plan": None,
        "errors": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Trigger orchestrator in background without blocking request
    task = asyncio.create_task(_run_orchestrator(event_id, config))
    _running_tasks[event_id] = task

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

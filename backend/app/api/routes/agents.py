"""Agents API routes — /api/agents/*

POST /api/agents/run          — run full orchestration, return plan (blocking)
POST /api/agents/run/stream   — run with SSE streaming per agent completion
GET  /api/agents/             — list all agents
GET  /api/agents/{name}/info  — agent metadata
"""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.data.models import EventConfig
from app.agents.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run")
async def run_agents(config: EventConfig):
    """
    Run all 7 agents for the given event config.
    Blocking — waits for all agents to complete before returning.
    For real-time updates use /run/stream or the WebSocket endpoint.
    """
    try:
        orch = Orchestrator()
        plan = await orch.run(config)
        return plan
    except Exception as exc:
        logger.error(f"Orchestrator error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/run/stream")
async def run_agents_stream(config: EventConfig):
    """
    Server-Sent Events stream — yields one JSON line per agent as it completes.
    Frontend can listen with EventSource or fetch + ReadableStream.
    """
    async def _generate() -> AsyncGenerator[str, None]:
        try:
            orch = Orchestrator()
            async for update in orch.run_stream(config):
                yield f"data: {json.dumps(update, default=str)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


AGENT_INFO = {
    "sponsor_agent":   {"name": "Sponsor Agent",   "description": "Recommends sponsors based on event profile and historical data", "wave": 1},
    "speaker_agent":   {"name": "Speaker Agent",   "description": "Recommends speakers, artists, or athletes by domain",           "wave": 1},
    "venue_agent":     {"name": "Venue Agent",     "description": "Recommends venues by capacity, location, and past usage",       "wave": 1},
    "exhibitor_agent": {"name": "Exhibitor Agent", "description": "Recommends exhibitor companies for booth space",                "wave": 1},
    "pricing_agent":   {"name": "Pricing Agent",   "description": "Projects ticket tiers, revenue, and break-even analysis",      "wave": 2},
    "ops_agent":       {"name": "Ops Agent",       "description": "Builds event schedule and operations resource plan",            "wave": 2},
    "gtm_agent":       {"name": "GTM Agent",       "description": "Builds go-to-market strategy and finds communities",           "wave": 2},
}


@router.get("/")
def list_agents():
    return list(AGENT_INFO.values())


@router.get("/{agent_name}/info")
def agent_info(agent_name: str):
    info = AGENT_INFO.get(agent_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return info

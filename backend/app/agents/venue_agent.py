"""Venue Agent — recommends venues for an event.

Flow:
  1. Pull venues from Supabase matching city/country + capacity
  2. Also look at where similar events were held
  3. LLM ranks + enriches with search_web for availability/pricing
  4. Returns scored VenueResult list
"""

from __future__ import annotations

import json
import logging

from groq import Groq

from app.agents.base_agent import BaseAgent
from app.config import get_settings
from app.data.database import get_db
from app.data.models import EventConfig
from app.services.tools import TOOL_SCHEMAS, call_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Venue Intelligence Agent for an AI-powered event planning platform.

Recommend the best venues for an event based on capacity, location, type, and past usage.
Use search_web to find current pricing, availability, and reviews.

Output ONLY valid JSON:
[
  {
    "rank": 1,
    "name": "...",
    "city": "...",
    "country": "...",
    "venue_type": "convention_center|hotel|stadium|club|outdoor|arena",
    "estimated_capacity": 0,
    "why": "1-2 sentence fit explanation",
    "daily_rate_estimate": "₹X - ₹Y or $X - $Y",
    "amenities": ["WiFi", "AV Equipment", "Parking"],
    "past_events": ["Event A 2025"],
    "availability_note": "likely available|check with venue",
    "total_score": 0.0-1.0,
    "scores": {"capacity_fit": 0.0, "location": 0.0, "budget_fit": 0.0, "past_usage": 0.0}
  }
]
"""


class VenueAgent(BaseAgent):
    name = "venue_agent"
    description = "Recommends venues based on event size, location, type, and historical usage"

    async def execute(self, config: EventConfig, shared_state: dict) -> dict:
        db       = get_db()
        client   = Groq(api_key=get_settings().groq_api_key)
        settings = get_settings()

        # ── Tier 1: RAG — venues from DB ──────────────────────────────────────
        db_venues = db.get_venues(
            city=config.city,
            country=config.geography if not config.city else None,
            min_capacity=config.target_audience // 2,
            limit=20,
        )

        # Also get venues from similar past events
        similar_events = db.get_events(
            domain=config.domain.value,
            city=config.city,
            limit=5,
        )
        past_venues: list[dict] = []
        seen_venues: set[str] = set()
        for event in similar_events:
            vname = event.get("venue_name")
            city  = event.get("city")
            if vname and vname not in seen_venues:
                seen_venues.add(vname)
                past_venues.append({
                    "name":        vname,
                    "city":        city,
                    "country":     event.get("country"),
                    "used_by":     event["name"],
                    "event_date":  event.get("start_date"),
                    "attendance":  event.get("estimated_attendance"),
                })

        context = {
            "event": {
                "name":            config.event_name or f"{config.category} Event",
                "domain":          config.domain.value,
                "category":        config.category,
                "geography":       config.geography,
                "city":            config.city,
                "target_audience": config.target_audience,
                "budget":          f"{config.budget_min}-{config.budget_max} {config.currency}" if config.budget_min else "Not specified",
                "dates":           f"{config.start_date} to {config.end_date}" if config.start_date else "TBD",
            },
            "venues_in_database": [
                {"name": v["name"], "city": v["city"], "country": v["country"]}
                for v in db_venues
            ],
            "venues_from_similar_events": past_venues[:5],
        }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Event context:\n{json.dumps(context, indent=2)}\n\n"
                    "Research the top venue candidates using tools (search for pricing, "
                    "capacity, availability), then return your ranked JSON recommendations."
                ),
            },
        ]

        # ── Tier 2: ReAct loop ────────────────────────────────────────────────
        venues = []
        for _ in range(5):
            response = client.chat.completions.create(
                model=settings.default_model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1500,
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
                    {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ]})
                for tc in msg.tool_calls:
                    args   = json.loads(tc.function.arguments)
                    result = call_tool(tc.function.name, args)
                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tc.id,
                        "content":      json.dumps(result, default=str)[:600],
                    })
                continue

            text = (msg.content or "").strip()
            try:
                start = text.find("[")
                end   = text.rfind("]") + 1
                if start >= 0 and end > start:
                    venues = json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.warning("VenueAgent: could not parse LLM response")
            break

        return {
            "venues":          venues,
            "total_found":     len(venues),
            "db_venues_used":  len(db_venues),
            "past_venues":     past_venues,
            "confidence":      0.8 if venues else 0.3,
            "explanation":     f"Found {len(venues)} venue recommendations",
            "data_sources":    ["supabase_venues", "exa_web_search"],
        }

"""Event Ops Agent — builds schedule, detects conflicts, resource plan.

Uses Wave 1 outputs (speakers, venues) to create a day-by-day schedule
and identify operational requirements.
"""

from __future__ import annotations

import json
import logging

from groq import Groq

from app.agents.base_agent import BaseAgent
from app.config import get_settings
from app.data.models import EventConfig
from app.services.tools import TOOL_SCHEMAS, call_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an Event Operations Agent for an event planning platform.

Build a realistic event schedule and operations plan using:
- Confirmed speakers/artists/athletes from the speaker agent
- Venue details from the venue agent
- Event config (dates, audience size, domain)

Output ONLY valid JSON:
{
  "schedule": [
    {
      "day": 1,
      "date": "YYYY-MM-DD",
      "slots": [
        {"time": "09:00", "slot_type": "registration", "title": "Registration & Welcome", "speaker": "", "room": "Main Hall"},
        {"time": "10:00", "slot_type": "keynote",      "title": "Opening Keynote",        "speaker": "Name", "room": "Main Stage"}
      ]
    }
  ],
  "conflicts_detected": 0,
  "conflicts_resolved": 0,
  "conflict_notes": [],
  "resource_plan": {
    "staff_required": 0,
    "av_equipment": ["item1"],
    "catering": "...",
    "security": "...",
    "estimated_ops_cost": "₹X - ₹Y"
  },
  "checklist": [
    {"task": "Book venue", "deadline": "8 weeks out", "owner": "Ops team"},
    {"task": "Send speaker invites", "deadline": "6 weeks out", "owner": "Program team"}
  ],
  "confidence": 0.0
}
"""


class OpsAgent(BaseAgent):
    name = "ops_agent"
    description = "Builds event schedule, detects conflicts, and creates operations resource plan"

    async def execute(self, config: EventConfig, shared_state: dict) -> dict:
        client   = Groq(api_key=get_settings().groq_api_key)
        settings = get_settings()

        speakers = shared_state.get("speaker_agent", {}).get("talents", [])
        venues   = shared_state.get("venue_agent",   {}).get("venues",  [])

        context = {
            "event": {
                "name":            config.event_name or f"{config.category} Event",
                "domain":          config.domain.value,
                "category":        config.category,
                "start_date":      config.start_date or "TBD",
                "end_date":        config.end_date or "TBD",
                "target_audience": config.target_audience,
                "city":            config.city,
            },
            "confirmed_speakers": [
                {"name": s.get("name"), "role": s.get("role")}
                for s in speakers[:8]
            ],
            "primary_venue": venues[0] if venues else None,
        }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Event context:\n{json.dumps(context, indent=2)}\n\n"
                    "Build a detailed schedule and ops plan. Return JSON."
                ),
            },
        ]

        ops = {}
        # Ops agent usually doesn't need web tools — LLM can reason from context
        response = client.chat.completions.create(
            model=settings.default_model,
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        text = (response.choices[0].message.content or "").strip()
        try:
            start = text.find("{")
            end   = text.rfind("}") + 1
            if start >= 0 and end > start:
                ops = json.loads(text[start:end])
        except json.JSONDecodeError:
            logger.warning("OpsAgent: could not parse LLM response")

        return {
            **ops,
            "confidence":   ops.get("confidence", 0.75),
            "explanation":  f"Schedule and ops plan for {config.target_audience} attendees",
            "data_sources": ["speaker_agent_results", "venue_agent_results"],
        }

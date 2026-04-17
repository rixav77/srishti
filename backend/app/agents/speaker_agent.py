"""Speaker / Artist / Athlete Agent.

Recommends speakers (conferences), artists (music festivals),
or athletes/teams (sporting events) based on domain.

Flow:
  1. Pull talents from similar past events (Supabase)
  2. LLM ranks + enriches via search_web / get_artist_stats tool calls
  3. Returns scored talent list with role suggestions
"""

from __future__ import annotations

import json
import logging

from groq import Groq

from app.agents.base_agent import BaseAgent
from app.config import get_settings
from app.data.database import get_db
from app.data.models import AgentOutput, EventConfig
from app.services.tools import TOOL_SCHEMAS, call_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = {
    "conference": """You are a Speaker Intelligence Agent for a conference planning platform.

Recommend speakers based on the event's topic, audience size, and geography.
Use tools to find current speaker availability, fee ranges, and recent talks.

Output ONLY valid JSON:
[
  {
    "rank": 1,
    "name": "...",
    "title": "...",
    "organization": "...",
    "role": "keynote|panel|workshop",
    "topics": ["topic1", "topic2"],
    "why": "1-2 sentence fit explanation",
    "estimated_fee_range": "$X - $Y USD",
    "linkedin_url": "...",
    "followers": 0,
    "total_score": 0.0-1.0,
    "scores": {"relevance": 0.0, "reach": 0.0, "availability": 0.0}
  }
]""",

    "music_festival": """You are an Artist Booking Agent for a music festival platform.

Recommend artists/performers based on genre, audience size, and festival location.
Use tools to find Spotify monthly listeners, recent tours, and booking availability.

Output ONLY valid JSON:
[
  {
    "rank": 1,
    "name": "...",
    "role": "headliner|supporting|opener",
    "genre": "...",
    "why": "1-2 sentence fit explanation",
    "spotify_monthly_listeners": 0,
    "estimated_fee_range": "$X - $Y USD",
    "recent_tours": ["Tour A 2025"],
    "total_score": 0.0-1.0,
    "scores": {"popularity": 0.0, "genre_fit": 0.0, "audience_match": 0.0}
  }
]""",

    "sporting_event": """You are a Sports Talent Agent for an event planning platform.

Recommend athletes, teams, or commentators based on sport, location, and audience size.
Use tools to find current team rankings, athlete stats, and availability.

Output ONLY valid JSON:
[
  {
    "rank": 1,
    "name": "...",
    "sport": "...",
    "role": "athlete|team|commentator|coach",
    "why": "1-2 sentence fit explanation",
    "current_ranking": "...",
    "estimated_fee_range": "$X - $Y USD",
    "total_score": 0.0-1.0,
    "scores": {"relevance": 0.0, "popularity": 0.0, "availability": 0.0}
  }
]""",
}


class SpeakerAgent(BaseAgent):
    name = "speaker_agent"
    description = "Recommends speakers, artists, or athletes based on event domain and profile"

    async def execute(self, config: EventConfig, shared_state: dict) -> dict:
        db       = get_db()
        client   = Groq(api_key=get_settings().groq_api_key)
        settings = get_settings()
        domain   = config.domain.value

        # ── Tier 1: RAG — pull talents from similar events ────────────────────
        similar_events = db.get_events(
            domain=domain,
            city=config.city,
            limit=15,
        )
        if not similar_events:
            similar_events = db.get_events(domain=domain, limit=15)

        talent_counts: dict[str, dict] = {}
        for event in similar_events[:10]:
            for t in db.get_event_talents(event["id"]):
                name = t["name"]
                if name not in talent_counts:
                    talent_counts[name] = {"count": 0, "type": t.get("type"), "role": t.get("role")}
                talent_counts[name]["count"] += 1

        top_talents = sorted(talent_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:15]

        talent_type = {"conference": "speakers", "music_festival": "artists", "sporting_event": "athletes"}[domain]

        context = {
            "event": {
                "name":            config.event_name or f"{config.category} Event",
                "domain":          domain,
                "category":        config.category,
                "geography":       config.geography,
                "city":            config.city,
                "target_audience": config.target_audience,
                "dates":           f"{config.start_date} to {config.end_date}" if config.start_date else "TBD",
            },
            f"past_{talent_type}_from_similar_events": [
                {"name": name, "appearances": data["count"], "typical_role": data["role"]}
                for name, data in top_talents
            ],
            "similar_events_count": len(similar_events),
        }

        system_prompt = SYSTEM_PROMPTS.get(domain, SYSTEM_PROMPTS["conference"])

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Event context:\n{json.dumps(context, indent=2)}\n\n"
                    f"Research the top {talent_type} candidates using tools, "
                    "then return your ranked JSON recommendations."
                ),
            },
        ]

        # ── Tier 2: ReAct loop ────────────────────────────────────────────────
        talents = []
        for _ in range(5):
            response = client.chat.completions.create(
                model=settings.fast_model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=2000,
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
                        "content":      json.dumps(result, default=str)[:2000],
                    })
                continue

            text = (msg.content or "").strip()
            try:
                start = text.find("[")
                end   = text.rfind("]") + 1
                if start >= 0 and end > start:
                    talents = json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.warning("SpeakerAgent: could not parse LLM response")
            break

        return {
            "talents":          talents,
            "talent_type":      talent_type,
            "total_found":      len(talents),
            "rag_events_used":  len(similar_events),
            "confidence":       0.8 if talents else 0.3,
            "explanation":      f"Found {len(talents)} {talent_type} based on {len(similar_events)} similar events",
            "data_sources":     ["supabase_events", "exa_web_search"],
        }

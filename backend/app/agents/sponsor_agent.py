"""Sponsor Agent — recommends sponsors for an event.

Flow:
  1. Pull similar past events from Supabase (by domain + category + geography)
  2. Collect sponsors that appeared at those events
  3. Ask Groq LLM to rank + enrich them using tool calls (search_web, get_company_info)
  4. Return scored SponsorResult list
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

SYSTEM_PROMPT = """You are a Sponsor Intelligence Agent for an AI-powered event planning platform.

Your job: recommend the best sponsors for an event based on historical data and live research.

You have access to tools:
- search_web: find current sponsor budgets, recent sponsorships, company news
- get_company_info: get company industry, size, headquarters

Process:
1. Review the event config and past sponsors provided in context
2. Call tools to enrich the top 3-5 sponsor candidates with current info
3. Return a JSON array of ranked sponsor recommendations

Output ONLY valid JSON in this exact format:
[
  {
    "rank": 1,
    "company_name": "...",
    "industry": "...",
    "recommended_tier": "title|gold|silver|bronze",
    "why": "1-2 sentence explanation of fit",
    "past_sponsorships": ["Event A 2025", "Event B 2026"],
    "estimated_budget_range": "₹X - ₹Y lakhs or $X - $Y USD",
    "total_score": 0.0-1.0,
    "scores": {"relevance": 0.0, "budget_fit": 0.0, "audience_match": 0.0}
  }
]
"""


class SponsorAgent(BaseAgent):
    name = "sponsor_agent"
    description = "Recommends and ranks potential sponsors based on event profile and historical data"

    async def execute(self, config: EventConfig, shared_state: dict) -> dict:
        db     = get_db()
        client = Groq(api_key=get_settings().groq_api_key)
        settings = get_settings()

        # ── Tier 1: RAG — pull similar events + their sponsors ────────────────
        similar_events = db.get_events(
            domain=config.domain.value,
            city=config.city,
            limit=15,
        )
        if not similar_events and config.city:
            # Widen to country
            similar_events = db.get_events(domain=config.domain.value, limit=15)

        # Collect sponsors from those events
        sponsor_counts: dict[str, int] = {}
        for event in similar_events[:10]:
            for sp in db.get_event_sponsors(event["id"]):
                name = sp["company_name"]
                sponsor_counts[name] = sponsor_counts.get(name, 0) + 1

        # Sort by frequency across similar events
        top_sponsors = sorted(sponsor_counts.items(), key=lambda x: x[1], reverse=True)[:15]

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
            "past_sponsors_from_similar_events": [
                {"name": name, "appearances": count}
                for name, count in top_sponsors
            ],
            "similar_events_count": len(similar_events),
        }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Event context:\n{json.dumps(context, indent=2)}\n\n"
                    "Research the top sponsor candidates using tools, then return your ranked JSON recommendations."
                ),
            },
        ]

        # ── Tier 2: ReAct loop — LLM calls tools until it returns JSON ────────
        sponsors = []
        for _ in range(5):  # max 5 tool-call rounds
            response = client.chat.completions.create(
                model=settings.default_model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=2000,
            )
            msg = response.choices[0].message

            # If the LLM made tool calls, execute them and continue
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

            # No tool calls — parse final JSON answer
            text = (msg.content or "").strip()
            try:
                # Extract JSON array from response
                start = text.find("[")
                end   = text.rfind("]") + 1
                if start >= 0 and end > start:
                    sponsors = json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.warning("SponsorAgent: could not parse LLM response as JSON")
            break

        return {
            "sponsors":       sponsors,
            "total_found":    len(sponsors),
            "rag_events_used": len(similar_events),
            "confidence":     0.8 if sponsors else 0.3,
            "explanation":    f"Found {len(sponsors)} sponsor recommendations based on {len(similar_events)} similar events",
            "data_sources":   ["supabase_events", "exa_web_search"],
        }

"""Exhibitor Agent — recommends exhibitors/vendors for an event.

Exhibitors are companies that set up booths: startups, product vendors,
tech companies, NGOs, etc. Most relevant for conferences and expos.

Flow:
  1. Pull sponsor companies from similar events (repurposed as exhibitor pool)
  2. LLM enriches with company info and recommends booth tiers
  3. Returns scored ExhibitorResult list
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

SYSTEM_PROMPT = """You are an Exhibitor Intelligence Agent for an event planning platform.

Recommend companies that should exhibit at this event — product demos, booths, sponsor tables.
Focus on companies whose products align with the event's audience.
Use get_company_info and search_web to research the best candidates.

Output ONLY valid JSON:
[
  {
    "rank": 1,
    "company_name": "...",
    "category": "startup|enterprise|tools|research|individual",
    "industry": "...",
    "booth_tier": "premium|standard|startup",
    "why": "1-2 sentence fit explanation",
    "estimated_booth_cost": "₹X - ₹Y or $X - $Y",
    "exhibition_history": ["Event A 2025"],
    "contact_approach": "LinkedIn outreach|email|event portal",
    "total_score": 0.0-1.0,
    "scores": {"audience_fit": 0.0, "product_relevance": 0.0, "budget_likelihood": 0.0}
  }
]
"""


class ExhibitorAgent(BaseAgent):
    name = "exhibitor_agent"
    description = "Recommends companies to exhibit at the event based on audience fit"

    async def execute(self, config: EventConfig, shared_state: dict) -> dict:
        db       = get_db()
        client   = Groq(api_key=get_settings().groq_api_key)
        settings = get_settings()

        # ── Tier 1: RAG — sponsors from similar events as exhibitor pool ──────
        similar_events = db.get_events(
            domain=config.domain.value,
            city=config.city,
            limit=15,
        )
        if not similar_events:
            similar_events = db.get_events(domain=config.domain.value, limit=15)

        company_pool: dict[str, int] = {}
        for event in similar_events[:10]:
            for sp in db.get_event_sponsors(event["id"]):
                name = sp["company_name"]
                company_pool[name] = company_pool.get(name, 0) + 1

        top_companies = sorted(company_pool.items(), key=lambda x: x[1], reverse=True)[:15]

        # Also use sponsor results from shared state if sponsor agent ran first
        sponsor_results = shared_state.get("sponsor_agent", {}).get("sponsors", [])
        sponsor_names   = [s.get("company_name") for s in sponsor_results if s.get("company_name")]

        context = {
            "event": {
                "name":            config.event_name or f"{config.category} Event",
                "domain":          config.domain.value,
                "category":        config.category,
                "geography":       config.geography,
                "city":            config.city,
                "target_audience": config.target_audience,
                "dates":           f"{config.start_date} to {config.end_date}" if config.start_date else "TBD",
            },
            "companies_from_similar_events": [
                {"name": name, "appearances": count}
                for name, count in top_companies
            ],
            "confirmed_sponsors": sponsor_names,
            "note": "Exhibitors are separate from sponsors — they pay for booth space to demo products",
        }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Event context:\n{json.dumps(context, indent=2)}\n\n"
                    "Research the top exhibitor candidates, then return your ranked JSON list."
                ),
            },
        ]

        # ── Tier 2: ReAct loop ────────────────────────────────────────────────
        exhibitors = []
        for _ in range(4):
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
                    exhibitors = json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.warning("ExhibitorAgent: could not parse LLM response")
            break

        return {
            "exhibitors":      exhibitors,
            "total_found":     len(exhibitors),
            "rag_events_used": len(similar_events),
            "confidence":      0.75 if exhibitors else 0.3,
            "explanation":     f"Found {len(exhibitors)} exhibitor recommendations",
            "data_sources":    ["supabase_events", "exa_web_search"],
        }

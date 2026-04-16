"""Pricing & Footfall Agent — projects revenue, ticket tiers, break-even.

Uses Wave 1 outputs (venue capacity, sponsor commitments, audience size)
to model ticket pricing scenarios.
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

SYSTEM_PROMPT = """You are a Pricing & Revenue Intelligence Agent for an event planning platform.

Design optimal ticket pricing tiers and project revenue using:
- Event config (audience size, geography, domain, budget)
- Venue capacity from venue agent results
- Sponsor commitments from sponsor agent results
- Historical pricing from similar events

Use search_web to find current ticket prices for comparable events.

Output ONLY valid JSON:
{
  "tiers": [
    {"name": "Early Bird", "price": 0, "currency": "INR", "allocation_pct": 30, "estimated_sales": 0, "revenue": 0},
    {"name": "General",    "price": 0, "currency": "INR", "allocation_pct": 50, "estimated_sales": 0, "revenue": 0},
    {"name": "VIP",        "price": 0, "currency": "INR", "allocation_pct": 20, "estimated_sales": 0, "revenue": 0}
  ],
  "total_projected_revenue": 0,
  "sponsor_revenue_estimate": 0,
  "total_event_revenue": 0,
  "estimated_costs": 0,
  "break_even_attendees": 0,
  "estimated_total_attendees": 0,
  "confidence": 0.0,
  "assumptions": ["assumption 1", "assumption 2"],
  "comparable_events": [{"name": "...", "price_range": "..."}]
}
"""


class PricingAgent(BaseAgent):
    name = "pricing_agent"
    description = "Projects ticket pricing tiers, revenue, and break-even analysis"

    async def execute(self, config: EventConfig, shared_state: dict) -> dict:
        db       = get_db()
        client   = Groq(api_key=get_settings().groq_api_key)
        settings = get_settings()

        # Pull similar events for price benchmarking
        similar_events = db.get_events(
            domain=config.domain.value,
            city=config.city,
            limit=10,
        )
        price_benchmarks = [
            {
                "name":       e["name"],
                "city":       e.get("city"),
                "price_min":  e.get("ticket_price_min"),
                "price_max":  e.get("ticket_price_max"),
                "currency":   e.get("currency"),
                "attendance": e.get("estimated_attendance"),
            }
            for e in similar_events
            if e.get("ticket_price_min")
        ]

        context = {
            "event": {
                "name":            config.event_name or f"{config.category} Event",
                "domain":          config.domain.value,
                "category":        config.category,
                "geography":       config.geography,
                "city":            config.city,
                "target_audience": config.target_audience,
                "budget":          f"{config.budget_min}-{config.budget_max} {config.currency}" if config.budget_min else "Not specified",
                "currency":        config.currency,
            },
            "venue_capacity":    shared_state.get("venue_agent", {}).get("venues", [{}])[0].get("estimated_capacity") if shared_state.get("venue_agent", {}).get("venues") else None,
            "sponsor_count":     len(shared_state.get("sponsor_agent", {}).get("sponsors", [])),
            "price_benchmarks":  price_benchmarks[:8],
        }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Event context:\n{json.dumps(context, indent=2)}\n\n"
                    "Search for current pricing of comparable events, then return your pricing JSON."
                ),
            },
        ]

        pricing = {}
        for _ in range(4):
            response = client.chat.completions.create(
                model=settings.default_model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.2,
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
                        "content":      json.dumps(result, default=str)[:2000],
                    })
                continue

            text = (msg.content or "").strip()
            try:
                start = text.find("{")
                end   = text.rfind("}") + 1
                if start >= 0 and end > start:
                    pricing = json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.warning("PricingAgent: could not parse LLM response")
            break

        return {
            **pricing,
            "confidence":    pricing.get("confidence", 0.7),
            "explanation":   f"Pricing model based on {len(price_benchmarks)} comparable events",
            "data_sources":  ["supabase_events", "exa_web_search"],
        }

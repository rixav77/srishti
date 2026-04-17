"""GTM (Go-To-Market) & Community Agent.

Identifies communities to promote the event and builds a marketing strategy.
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

SYSTEM_PROMPT = """You are a GTM & Community Intelligence Agent for an event planning platform.

Build a go-to-market strategy: identify communities to reach, messaging angles,
promotional channels, and a timeline.

Use search_web to find active communities (Discord, LinkedIn, Reddit, Slack, Meetup)
relevant to the event's domain and geography.

Output ONLY valid JSON:
{
  "communities": [
    {
      "name": "...",
      "platform": "discord|linkedin|reddit|slack|meetup|whatsapp",
      "url": "...",
      "estimated_members": 0,
      "activity_level": "high|medium|low",
      "why": "...",
      "partnership_suggestion": "post|sponsor newsletter|host meetup"
    }
  ],
  "strategy_phases": [
    {"phase": "Pre-launch", "timeline": "8 weeks out", "actions": ["action1", "action2"]},
    {"phase": "Launch",     "timeline": "4 weeks out", "actions": ["action1"]},
    {"phase": "Push",       "timeline": "1 week out",  "actions": ["action1"]}
  ],
  "messaging": {
    "tagline": "...",
    "value_props": ["prop1", "prop2", "prop3"],
    "target_personas": ["persona1", "persona2"]
  },
  "estimated_reach": 0,
  "confidence": 0.0
}
"""


class GTMAgent(BaseAgent):
    name = "gtm_agent"
    description = "Builds go-to-market strategy and finds communities to promote the event"

    async def execute(self, config: EventConfig, shared_state: dict) -> dict:
        client   = Groq(api_key=get_settings().groq_api_key)
        settings = get_settings()

        confirmed_speakers  = shared_state.get("speaker_agent",   {}).get("talents",    [])
        confirmed_sponsors  = shared_state.get("sponsor_agent",   {}).get("sponsors",   [])

        context = {
            "event": {
                "name":            config.event_name or f"{config.category} Event",
                "domain":          config.domain.value,
                "category":        config.category,
                "geography":       config.geography,
                "city":            config.city,
                "target_audience": config.target_audience,
                "dates":           f"{config.start_date} to {config.end_date}" if config.start_date else "TBD",
                "description":     config.description,
            },
            "confirmed_speakers": [s.get("name") for s in confirmed_speakers[:5]],
            "confirmed_sponsors": [s.get("company_name") for s in confirmed_sponsors[:5]],
        }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Event context:\n{json.dumps(context, indent=2)}\n\n"
                    "Find relevant communities and build a GTM strategy. Return JSON."
                ),
            },
        ]

        gtm = {}
        for _ in range(4):
            response = client.chat.completions.create(
                model=settings.default_model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.4,
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
                start = text.find("{")
                end   = text.rfind("}") + 1
                if start >= 0 and end > start:
                    gtm = json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.warning("GTMAgent: could not parse LLM response")
            break

        return {
            **gtm,
            "confidence":  gtm.get("confidence", 0.7),
            "explanation": f"GTM strategy for {config.category} in {config.geography}",
            "data_sources": ["exa_web_search"],
        }

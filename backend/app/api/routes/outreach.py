"""Outreach draft generation — personalized email + LinkedIn message via LLM.

PDF requirement: "Autonomous outreach drafts (not generic)"
Each draft uses the target's profile + event context + relevance score.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from groq import Groq
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


class OutreachRequest(BaseModel):
    target_type: str  # "sponsor" | "speaker" | "exhibitor" | "community"
    target_name: str
    target_context: dict = {}
    event_name: str = "Event"
    event_category: str = ""
    event_geography: str = ""
    event_audience: int = 500
    event_dates: str = "TBD"
    recommended_tier: str = ""
    relevance_reason: str = ""


class OutreachDraft(BaseModel):
    email_subject: str
    email_body: str
    linkedin_message: str


class OutreachResponse(BaseModel):
    target: str
    target_type: str
    drafts: OutreachDraft | None
    error: str | None = None


SYSTEM_PROMPT = """You are a professional event outreach writer.

Write personalized, non-generic outreach messages for event partnerships.
Use the recipient's specific background and the event's details.

Rules:
- Be professional but warm
- Reference the recipient's actual past activities / known facts
- Never use cliches like "exciting opportunity" or "synergy"
- Email body: 150-200 words max
- LinkedIn message: 60 words max
- Always include a clear call-to-action (15-min call, quick chat, etc.)

Return JSON with EXACTLY this shape:
{
  "email_subject": "...",
  "email_body": "...",
  "linkedin_message": "..."
}
"""


def _build_prompt(req: OutreachRequest) -> str:
    type_label = {
        "sponsor": "sponsorship partnership",
        "speaker": "speaking invitation",
        "exhibitor": "exhibition booth",
        "community": "community partnership",
    }.get(req.target_type, "partnership")

    context_str = ""
    if req.target_context:
        context_str = f"\nKnown info about {req.target_name}:\n"
        for k, v in req.target_context.items():
            context_str += f"  - {k}: {v}\n"

    return f"""Write a {type_label} outreach for:

Recipient: {req.target_name}
Type: {req.target_type}
{f"Recommended tier: {req.recommended_tier}" if req.recommended_tier else ""}
{f"Why they're a fit: {req.relevance_reason}" if req.relevance_reason else ""}
{context_str}
Event details:
- Name: {req.event_name}
- Category: {req.event_category}
- Location: {req.event_geography}
- Expected attendance: {req.event_audience}
- Dates: {req.event_dates}

Generate the email subject, email body, and LinkedIn message. Return JSON only."""


@router.post("/generate", response_model=OutreachResponse)
async def generate_outreach(request: OutreachRequest):
    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)

    try:
        response = client.chat.completions.create(
            model=settings.fast_model,  # 8B is fine for text generation
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_prompt(request)},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
            max_tokens=800,
        )

        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)

        return OutreachResponse(
            target=request.target_name,
            target_type=request.target_type,
            drafts=OutreachDraft(
                email_subject=parsed.get("email_subject", ""),
                email_body=parsed.get("email_body", ""),
                linkedin_message=parsed.get("linkedin_message", ""),
            ),
        )

    except Exception as e:
        logger.error(f"Outreach generation failed: {e}")
        return OutreachResponse(
            target=request.target_name,
            target_type=request.target_type,
            drafts=None,
            error=str(e)[:200],
        )

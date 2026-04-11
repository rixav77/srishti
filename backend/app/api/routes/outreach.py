from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class OutreachRequest(BaseModel):
    event_id: str
    target_type: str  # "sponsor" | "speaker" | "exhibitor" | "community"
    target_name: str
    target_context: dict = {}


@router.post("/generate")
async def generate_outreach(request: OutreachRequest):
    # TODO: Generate personalized outreach draft via LLM
    return {
        "event_id": request.event_id,
        "target": request.target_name,
        "type": request.target_type,
        "drafts": None,
    }

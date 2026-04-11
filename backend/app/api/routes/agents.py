from fastapi import APIRouter

router = APIRouter()


@router.get("/{agent_name}/results")
async def get_agent_results(agent_name: str, event_id: str):
    # TODO: Retrieve agent results from event plan
    return {"agent": agent_name, "event_id": event_id, "results": None}

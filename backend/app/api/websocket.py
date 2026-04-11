from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()

# Active connections per event
_connections: dict[str, list[WebSocket]] = {}


async def broadcast_event(event_id: str, message: dict):
    connections = _connections.get(event_id, [])
    dead = []
    for ws in connections:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.remove(ws)


@router.websocket("/events/{event_id}/stream")
async def event_stream(websocket: WebSocket, event_id: str):
    await websocket.accept()
    _connections.setdefault(event_id, []).append(websocket)

    try:
        while True:
            # Keep connection alive, receive any client messages
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            # Client can send commands like {"action": "retry_agent", "agent": "sponsor"}
            if msg.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        _connections.get(event_id, []).remove(websocket)

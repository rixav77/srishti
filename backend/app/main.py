from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import events, agents, simulation, data, outreach
from app.api.websocket import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"Starting {settings.app_name}...")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Srishti API",
    description="AI-Powered Multi-Agent Event Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(data.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(outreach.router, prefix="/api/outreach", tags=["outreach"])
app.include_router(ws_router, prefix="/api/ws", tags=["websocket"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "srishti"}

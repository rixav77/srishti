# Srishti - AI-Powered Multi-Agent Event Intelligence Platform

> Hackathon: Pinch x IIT Roorkee - Technical General Championship 2026

An AI-powered multi-agent system that autonomously plans conferences, music festivals, and sporting events.

## Architecture

```
User Input → Orchestrator → 7 AI Agents (parallel) → Consolidated Event Plan
```

**7 Agents:** Sponsor | Speaker/Artist | Exhibitor | Venue | Pricing & Footfall | Community & GTM | Event Ops

**Key Features:**
- Domain-agnostic (Conferences, Music Festivals, Sporting Events)
- Multi-agent orchestration with LangGraph
- RAG-powered recommendations (Pinecone + BGE-M3)
- Real-time agent collaboration visualization
- Simulation dashboard (pricing, break-even, what-if)
- Autonomous outreach draft generation

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Groq (Llama 3.3 70B) - Free |
| Embeddings | BGE-M3 (local) - Free |
| Backend | FastAPI (Python) |
| Frontend | Next.js 14 + Tailwind + shadcn/ui |
| Database | Supabase (PostgreSQL) - Free |
| Vector DB | Pinecone - Free |
| Cache | Upstash Redis - Free |
| Orchestration | LangGraph |

## Setup

```bash
# 1. Clone
git clone https://github.com/rixav77/srishti.git
cd srishti

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example ../.env  # Fill in your API keys

# 3. Frontend
cd ../frontend
npm install

# 4. Run
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

## Project Structure

```
srishti/
├── backend/          # FastAPI + LangGraph agents
├── frontend/         # Next.js dashboard
├── data/             # Mandatory dataset (CSV/JSON)
├── domain_profiles/  # Domain-agnostic YAML configs
└── docs/             # Engineering documentation
```

## Team

Built for the Pinch x IIT Roorkee High Prep Problem Solving hackathon.

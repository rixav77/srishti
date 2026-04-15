# 06 - Tech Stack

---

## Complete Technology Choices

### Core Framework

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **LLM (primary)** | Groq — `llama-3.3-70b-versatile` | Free, ultra-fast inference (~2s), native tool/function calling |
| **LLM (fast)** | Groq — `llama-3.1-8b-instant` | For lightweight classification, normalization, cheap fallbacks |
| **Embeddings** | BGE-M3 via HuggingFace Inference API | Free, 1024 dims, strong semantic quality |
| **Live Tools** | Exa API (primary) + Tavily (fallback) | Agent-callable web search for freshness |
| **Agent Framework** | LangGraph + LangChain | Stateful multi-agent orchestration, checkpointing, HITL |
| **Backend API** | FastAPI (Python) | Async, auto-docs, perfect for LangChain ecosystem |
| **Frontend** | Vite + React 18 + shadcn/ui | Already scaffolded, fast dev loop |
| **Database** | Supabase (PostgreSQL) | Free tier, real-time subscriptions, hosted |
| **Vector DB** | Pinecone | Managed, free (100K vectors), metadata filtering |
| **Cache/Queue** | Upstash Redis | Serverless Redis, free tier, live-data caching |

### Data & Scraping

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Web Scraping** | Playwright (Python) | JS-rendered pages, stealth mode, reliable |
| **HTTP Client** | httpx | Async, modern Python HTTP |
| **HTML Parsing** | BeautifulSoup4 | Simple, battle-tested |
| **Background Jobs** | Celery + Redis | Distributed task queue for scraping jobs |
| **Data Validation** | Pydantic v2 | Schema validation, serialization, type safety |
| **Data Export** | pandas | CSV/JSON export for mandatory deliverable |

### AI/ML

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **RAG Pipeline (Tier 1)** | LangChain + Pinecone + Supabase | Hybrid retrieval: semantic vectors + SQL joins |
| **Tools Layer (Tier 2)** | Exa API + Tavily + custom tool functions | Live web search & scraping, invoked via Groq function-calling |
| **Agent Memory** | LangGraph Checkpoints + Pinecone | Session memory + long-term episodic memory |
| **Predictive Models** | scikit-learn or rule-based | Sufficient for hackathon, no training data issues |
| **Outreach Generation** | Groq LLM prompting | High-quality personalized text generation |
| **Scoring/Ranking** | Custom Python (NumPy) | Lightweight multi-dimensional scoring |

### Knowledge Tiers (how agents fetch info)

| Tier | When to use | Tech | Speed | Freshness |
|------|------------|------|-------|-----------|
| **1. Static RAG** | Historical grounding ("who sponsored similar events?") | Pinecone + Supabase | Fast | Frozen at scrape time |
| **2. Live tools** | Current facts ("is Google Cloud's AI event budget growing in 2026?") | Exa / Tavily / Playwright | Slow | Real-time |
| **3. Agent memory** | Past sessions, user preferences | LangGraph checkpoints | Fast | Per-session |

Agents default to Tier 1 for speed, then call Tier 2 tools via function-calling when they detect missing or stale info.

### Frontend

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **UI Framework** | Next.js 14 + React 18 | SSR, API routes, fast iteration |
| **Styling** | Tailwind CSS + shadcn/ui | Rapid prototyping, polished look |
| **Charts** | Recharts or Nivo | Interactive charts for simulation dashboard |
| **Agent Visualization** | React Flow | Directed graph visualization for agent collaboration |
| **Real-time** | WebSocket (native) | Stream agent progress to frontend |
| **Forms** | React Hook Form + Zod | Type-safe form handling for event wizard |
| **State** | Zustand | Lightweight client state management |

### DevOps & Deployment

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Frontend Hosting** | Vercel | Free tier, Git-based deploys, edge network |
| **Backend Hosting** | Railway or Render | Free tier, Docker support, easy Python deploys |
| **CI/CD** | GitHub Actions | Free for public repos, standard |
| **Monitoring** | Built-in logging + Sentry (free) | Error tracking for demo reliability |

---

## Skill Alignment

The user has these relevant skills available:

| Skill | How We Use It |
|-------|--------------|
| **LangChain** | Core agent framework, RAG pipeline, tool integration |
| **LangGraph** | Multi-agent orchestration, state management |
| **Pinecone** | Vector DB for RAG, similarity search, metadata filtering |
| **ChromaDB** | Local development vector DB (fallback/testing) |
| **FAISS** | Fast local similarity search for development |
| **FastAPI** | Backend API server |
| **Next.js** | Frontend application |
| **Playwright** | Web scraping + E2E testing |
| **Claude API** | Primary LLM for agent reasoning and generation |

---

## API Key Requirements

| Service | Key Needed | Free Tier | Status |
|---------|-----------|-----------|--------|
| **Groq (LLM)** | `GROQ_API_KEY` | Free, high rate limits | Configured |
| **HuggingFace (embeddings)** | `HUGGINGFACEHUB_API_TOKEN` | Free | Configured |
| **Pinecone** | `PINECONE_API_KEY` | 100K vectors free | Configured |
| **Supabase** | `SUPABASE_URL` + `SUPABASE_KEY` | 500MB free | Configured |
| **Upstash Redis** | `REDIS_URL` | 10K commands/day free | Configured |
| **Exa (live web search)** | `EXA_API_KEY` | 1,000 searches free/month | To add |
| **Tavily (fallback search)** | `TAVILY_API_KEY` | 1,000 calls free/month | Optional |

---

## Project Structure

```
srishti/
├── README.md
├── ENGINEERING_DOCS.md
├── docker-compose.yml
├── .env.example
│
├── backend/                        # FastAPI + LangGraph
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py                 # FastAPI entrypoint
│   │   ├── config.py               # Settings + env vars
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── events.py       # POST /events/configure, GET /events/{id}
│   │   │   │   ├── agents.py       # GET /agents/{id}/results
│   │   │   │   ├── simulation.py   # POST /simulate/pricing, /breakeven
│   │   │   │   ├── data.py         # GET /datasets/events, /export
│   │   │   │   └── outreach.py     # POST /outreach/generate
│   │   │   └── websocket.py        # WS /ws/events/{id}/stream
│   │   │
│   │   ├── agents/                 # LangGraph agents
│   │   │   ├── orchestrator.py     # Supervisor + graph definition
│   │   │   ├── base_agent.py       # Base agent interface
│   │   │   ├── sponsor_agent.py
│   │   │   ├── speaker_agent.py
│   │   │   ├── exhibitor_agent.py
│   │   │   ├── venue_agent.py
│   │   │   ├── pricing_agent.py
│   │   │   ├── gtm_agent.py
│   │   │   └── ops_agent.py
│   │   │
│   │   ├── domain/                 # Domain-agnostic configs
│   │   │   ├── base.py             # DomainConfig base class
│   │   │   ├── conference.py
│   │   │   ├── music_festival.py
│   │   │   └── sporting_event.py
│   │   │
│   │   ├── data/                   # Data layer
│   │   │   ├── database.py         # PostgreSQL connection
│   │   │   ├── vector_store.py     # Pinecone operations
│   │   │   ├── cache.py            # Redis cache
│   │   │   └── models.py           # Pydantic schemas
│   │   │
│   │   ├── scrapers/               # Web scraping pipelines
│   │   │   ├── base_scraper.py
│   │   │   ├── eventbrite.py
│   │   │   ├── conftech.py
│   │   │   ├── linkedin.py
│   │   │   ├── crunchbase.py
│   │   │   ├── songkick.py
│   │   │   ├── spotify.py
│   │   │   └── google_maps.py
│   │   │
│   │   ├── ml/                     # ML models
│   │   │   ├── scoring.py          # Multi-dimensional scoring
│   │   │   ├── pricing_model.py    # Pricing optimization
│   │   │   ├── demand_model.py     # Attendance forecasting
│   │   │   └── simulation.py       # What-if scenario engine
│   │   │
│   │   └── services/               # Shared services
│   │       ├── embedding.py        # Embedding generation
│   │       ├── outreach.py         # Outreach draft generation
│   │       └── export.py           # CSV/JSON/PDF export
│   │
│   └── tests/
│       ├── test_agents/
│       ├── test_scrapers/
│       └── test_ml/
│
├── frontend/                       # Next.js application
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Landing / event wizard
│   │   │   ├── dashboard/
│   │   │   │   └── [eventId]/
│   │   │   │       ├── page.tsx    # Main dashboard
│   │   │   │       ├── agents/     # Agent results views
│   │   │   │       ├── simulation/ # Simulation dashboard
│   │   │   │       └── outreach/   # Outreach drafts
│   │   │   └── data/
│   │   │       └── page.tsx        # Dataset explorer
│   │   │
│   │   ├── components/
│   │   │   ├── wizard/             # Event configuration wizard
│   │   │   ├── dashboard/          # Dashboard components
│   │   │   ├── agents/             # Agent visualization
│   │   │   ├── simulation/         # Simulation controls + charts
│   │   │   └── ui/                 # shadcn/ui base components
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts     # Real-time agent updates
│   │   │   ├── useSimulation.ts    # Simulation state
│   │   │   └── useEventPlan.ts     # Event plan data
│   │   │
│   │   └── lib/
│   │       ├── api.ts              # API client
│   │       └── types.ts            # TypeScript types
│   │
│   └── public/
│       └── ...
│
├── data/                           # Mandatory dataset deliverable
│   ├── conferences_2025_2026.csv
│   ├── conferences_2025_2026.json
│   ├── music_festivals_2025_2026.csv
│   ├── music_festivals_2025_2026.json
│   ├── sporting_events_2025_2026.csv
│   ├── sporting_events_2025_2026.json
│   ├── DATA_SOURCES.md
│   └── scripts/
│       ├── scrape_conferences.py
│       ├── scrape_festivals.py
│       ├── scrape_sports.py
│       └── normalize_and_export.py
│
├── domain_profiles/                # Domain configuration YAML
│   ├── conference.yaml
│   ├── music_festival.yaml
│   └── sporting_event.yaml
│
└── docs/                           # Engineering documentation
    ├── ARCHITECTURE.md
    ├── AGENT_DESIGN.md
    ├── DATA_PIPELINE.md
    ├── API_REFERENCE.md
    └── DEMO_SCRIPT.md
```

---

## Development Environment Setup

```bash
# Prerequisites
# Python 3.11+, Node.js 18+, Docker (optional)

# Clone
git clone https://github.com/<team>/srishti.git
cd srishti

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # Fill in API keys

# Frontend
cd ../frontend
npm install
cp .env.example .env.local

# Database (Supabase - hosted, no local setup needed)
# Run migrations via Supabase dashboard or CLI

# Vector DB (Pinecone - hosted, no local setup needed)
# Create index via Pinecone dashboard

# Start development
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Celery workers (for scraping)
cd backend && celery -A app.workers worker --loglevel=info
```

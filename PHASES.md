# Srishti - Implementation Phases

> Each phase has clear deliverables. Team members can work on independent tracks in parallel.

---

## Phase 0: Project Setup [COMPLETED]

| Task | Status |
|------|--------|
| GitHub repo created | Done |
| Backend scaffolding (FastAPI + routes + models) | Done |
| Domain profiles (conference, music_festival, sporting_event YAML) | Done |
| Environment variables configured (Groq, Supabase, Pinecone, Redis, Exa) | Done |
| Backend deployed on Railway | Done |
| Health check working | Done |

**Live URL:** https://srishti-production.up.railway.app

---

## Phase 1: Data Foundation [COMPLETED]

### Phase 1A: Mandatory Dataset Collection [COMPLETED 2026-04-16]

| Task | Status |
|------|--------|
| Scrape conferences/hackathons (Devfolio, District, Mepass) | Done |
| Scrape music festivals (District, Skillboxes, Mepass) | Done |
| Scrape sporting events (District, Mepass, Skillboxes) | Done |
| Custom Exa-based search tools for famous events | Done |
| Enrich events (attendance, end dates, speakers/artists) | Done |
| Add curated famous events (NeurIPS, Coachella, FIFA WC, IPL, etc.) | Done |
| Export CSV + JSON for all 3 domains | Done |
| Write `data/DATA_SOURCES.md` | Done |

**Total: 241 events** (88 conf, 130 music, 23 sports) across 11 countries, 55 cities.

### Phase 1B: Database + Vector DB Setup [COMPLETED]

| Task | Status |
|------|--------|
| Supabase schema (7 tables + RLS + indexes) | Done |
| `database.py` facade with all query methods | Done |
| Seed Supabase: 241 events, 165 sponsors, 240 talents, 159 venues | Done |
| Pinecone: 241 vectors (1024 dims, multilingual-e5-large) | Done |
| 7 dataset API endpoints (stats, events, search, sponsors, talents, venues) | Done |

### Phase 1C: Verify Data Pipeline [COMPLETED]

All endpoints returning live Supabase data. Keyword search works across domains.

---

## Phase 1.5: Live Tools Layer [COMPLETED]

| Task | Status |
|------|--------|
| 4 live tools (search_web, scrape_page, get_company_info, get_artist_stats) | Done |
| Groq function-calling schemas + call_tool dispatcher | Done |
| Redis caching (1h TTL) on all tool calls | Done |

---

## Phase 2: AI Agents + Orchestration [COMPLETED]

| Task | Status |
|------|--------|
| 7 agents built (Sponsor, Speaker, Venue, Exhibitor, Pricing, GTM, Ops) | Done |
| Wave-based orchestrator (Wave 1 parallel, Wave 2 sequential) | Done |
| SSE streaming endpoint (`POST /api/agents/run/stream`) | Done |
| Blocking endpoint (`POST /api/agents/run`) | Done |
| All agents use Tier 1 RAG + Tier 2 Exa tools (ReAct loop) | Done |
| Deployed on Railway — all endpoints live | Done |

---

## Phase 3: Frontend Wiring + Features [CURRENT]

> Frontend UI shell exists. GeneratingPage calls real SSE endpoint.
> Agent result pages use real data when available, fall back to mock.

### 3A: End-to-End Testing [HIGH PRIORITY]

| Task | Status |
|------|--------|
| Run frontend locally, create a project, verify agents return real data | Pending |
| Fix any SSE/CORS issues between frontend ↔ Railway backend | Pending |
| Verify all 7 agent result pages display real data after pipeline runs | Pending |

### 3B: Outreach Draft Generation [HIGH PRIORITY]

> PDF says "autonomous outreach drafts (not generic)" — explicitly required.

| Task | Status |
|------|--------|
| Build `POST /api/outreach/generate` endpoint | Pending |
| LLM generates personalized email + LinkedIn message for sponsor/speaker | Pending |
| Wire outreach center page to real API | Pending |
| Add outreach drafts to agent outputs (sponsor + speaker agents) | Pending |

### 3C: Simulation Engine [HIGH PRIORITY]

> PDF says simulation dashboard is "particularly valued" for extra points.

| Task | Status |
|------|--------|
| Build real pricing simulation logic (not mock) — price elasticity model | Pending |
| Break-even calculator (fixed costs vs revenue, chart data) | Pending |
| Revenue projection engine (tickets + sponsors + exhibitors) | Pending |
| What-if scenario API: `POST /api/simulation/pricing` with real math | Pending |
| Wire simulation dashboard to real API (sliders → backend → chart update) | Pending |

### 3D: Agent Collaboration Visualization [MEDIUM PRIORITY]

> PDF calls this a "key differentiator" — live animated graph of agents working.

| Task | Status |
|------|--------|
| Add React Flow graph showing agent nodes + dependency edges | Pending |
| Animate nodes: waiting → running → completed/error (from SSE stream) | Pending |
| Show data flow between waves (Wave 1 → Wave 2 connections) | Pending |

### 3E: Dataset Explorer [MEDIUM PRIORITY]

| Task | Status |
|------|--------|
| Wire dataset explorer page to `GET /api/datasets/events` | Pending |
| Add domain/city/country filters | Pending |
| Show event detail modal with sponsors + talents | Pending |

---

## Phase 4: Polish + Deliverables [FINAL]

| Task | Status |
|------|--------|
| Deploy frontend to Vercel | Pending |
| End-to-end testing on deployed version (Vercel ↔ Railway) | Pending |
| Record demo video (3-5 min) | Pending |
| Write ENGINEERING_DOCS.md (architecture + agent logic) | Pending |
| Final repo cleanup + README update | Pending |

---

## Tech Stack Summary

| Component | Technology | Status |
|-----------|-----------|--------|
| LLM | Groq (Llama 3.3 70B + Llama 3.1 8B) | Live |
| Live web search | Exa API (neural search) | Live |
| On-demand scraping | crawl4ai + Playwright | Live |
| Backend | FastAPI (Python) on Railway | Live |
| Frontend | Vite + React + shadcn/ui | Shell built |
| Database | Supabase (PostgreSQL) — 241 events seeded | Live |
| Vector DB | Pinecone (1024 dims, multilingual-e5-large) | Live |
| Cache | Upstash Redis | Live |

## Knowledge Architecture (3 Tiers)

| Tier | Layer | Tech | When |
|------|-------|------|------|
| 1 | Static RAG | Pinecone (semantic) + Supabase (SQL) | Historical grounding — every agent starts here |
| 2 | Live tools | Exa neural search + crawl4ai scraper | Current verification — LLM calls on demand |
| 3 | Memory | Shared state dict passed between waves | Session state, Wave 2 agents use Wave 1 outputs |

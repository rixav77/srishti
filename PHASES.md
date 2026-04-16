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

## Phase 1: Data Foundation

### Phase 1A: Mandatory Dataset Collection [COMPLETED 2026-04-16]
> Scraping + Exa-based custom search tools. See `data/DATA_SOURCES.md`.

| Task | Status |
|------|--------|
| Scrape conferences/hackathons (Devfolio, District, Mepass) | Done |
| Scrape music festivals (District, Skillboxes, Mepass) | Done |
| Scrape sporting events (District, Mepass, Skillboxes) | Done |
| Custom Exa-based search tools for famous events | Done |
| Enrich events (attendance, end dates, speakers/artists) | Done |
| Add curated famous events (NeurIPS, Coachella, FIFA WC, IPL, etc.) | Done |
| Export `data/conferences_2025_2026.csv` + `.json` (88 events) | Done |
| Export `data/music_festivals_2025_2026.csv` + `.json` (130 events) | Done |
| Export `data/sporting_events_2025_2026.csv` + `.json` (23 events) | Done |
| Write `data/DATA_SOURCES.md` | Done |

**Final counts:**
- **Total: 241 events** (target 220+) ✓
- **Geographic spread: 11 countries, 55 cities**
- **Year distribution:** 13 × 2025, 228 × 2026
- **Attendance + end_dates: 100% coverage**
- **Sponsors: populated for 165 unique companies**
- **Speakers/artists: 240 unique talents across all domains**

### Phase 1B: Database + Vector DB Setup [COMPLETED]

| Task | Status |
|------|--------|
| Create Supabase schema — 7 tables (events, sponsors, event_sponsors, talents, event_talents, venues, communities) | Done |
| RLS policies + indexes on all tables | Done |
| Build `backend/app/data/database.py` — typed DB facade with all query methods | Done |
| Seed Supabase: 241 events, 165 sponsors, 240 talents, 159 venues | Done |
| Wire junction tables: 369 event→sponsor links, 270 event→talent links | Done |
| Generate embeddings + load into Pinecone (namespace: "events", 1024 dims) | Done |
| `GET /api/datasets/stats` — live counts from Supabase | Done |
| `GET /api/datasets/events` — paginated + filtered event list | Done |
| `GET /api/datasets/events/{id}` — full detail with sponsors + talents | Done |
| `GET /api/datasets/search` — keyword search across name/desc/category/venue | Done |
| `GET /api/datasets/sponsors` — sponsor list with filters | Done |
| `GET /api/datasets/talents` — talent list with type filter | Done |
| `GET /api/datasets/venues` — venue list with city/capacity filters | Done |

**Scripts created:**
- `scripts/sql/01_schema.sql` — full Supabase schema (run once in SQL editor)
- `scripts/seed_supabase.py` — idempotent Python seed script
- `scripts/seed_pinecone.py` — Pinecone vector upsert script

### Phase 1C: Verify Data Pipeline [COMPLETED]

| Task | Status |
|------|--------|
| Test DB queries return correct data | Done — all endpoints returning live Supabase data |
| Test keyword search works across domains | Done |
| Fixed `.env` path resolution in `config.py` | Done |

---

## Phase 1.5: Live Tools Layer [COMPLETED]

> Addresses the "static RAG" gap: agents fetch current info on demand via Exa + crawl4ai.

| Task | Status |
|------|--------|
| `EXA_API_KEY` configured in env | Done |
| `backend/app/services/tools.py` — 4 live tools implemented | Done |
| `search_web(query, num_results)` — Exa neural search | Done |
| `scrape_page(url)` — crawl4ai page fetch returning markdown | Done |
| `get_company_info(name)` — Exa company research | Done |
| `get_artist_stats(name)` — Exa artist/performer research | Done |
| Redis caching wrapper (1h TTL) on all tool calls | Done |
| Groq function-calling schemas (`TOOL_SCHEMAS`) for all 4 tools | Done |
| `call_tool(name, args)` dispatcher for ReAct loop | Done |

**Tool inventory:**

| Tool | Purpose | Used by |
|------|---------|---------|
| `search_web(query)` | Neural web search via Exa | All agents |
| `scrape_page(url)` | Fetch + parse page as markdown (crawl4ai) | Speaker, Venue agents |
| `get_company_info(name)` | Company overview, HQ, industry | Sponsor, Exhibitor agents |
| `get_artist_stats(name)` | Artist genre, Spotify listeners, tours | Speaker agent (music) |

---

## Phase 2: AI Agents [COMPLETED]

> All agents use Tier 1 RAG (Supabase SQL) + Tier 2 live tools (Exa) in a ReAct loop.
> Pattern: pull similar events from DB → LLM enriches with tool calls → return ranked JSON.

### Phase 2A: Wave 1 Agents (run in parallel) [COMPLETED]

| Task | Status |
|------|--------|
| `backend/app/agents/sponsor_agent.py` — RAG + ReAct, ranked sponsors with tiers | Done |
| `backend/app/agents/speaker_agent.py` — domain-aware (speaker/artist/athlete), RAG + ReAct | Done |
| `backend/app/agents/venue_agent.py` — venue DB + similar events + ReAct | Done |
| `backend/app/agents/exhibitor_agent.py` — sponsor pool + Wave 1 shared state | Done |

### Phase 2B: Wave 2 Agents (run sequentially, use Wave 1 outputs) [COMPLETED]

| Task | Status |
|------|--------|
| `backend/app/agents/pricing_agent.py` — benchmarks DB prices, projects 3 ticket tiers + revenue | Done |
| `backend/app/agents/gtm_agent.py` — finds communities, builds phased GTM strategy | Done |
| `backend/app/agents/ops_agent.py` — builds day-by-day schedule + resource plan | Done |

### Phase 2C: Orchestration [COMPLETED]

| Task | Status |
|------|--------|
| `backend/app/agents/orchestrator.py` — wave-based parallel + sequential execution | Done |
| Wave 1 parallel execution via `asyncio.gather` | Done |
| Wave 2 sequential execution with shared state passing | Done |
| SSE streaming via `run_stream()` async generator | Done |
| `POST /api/agents/run` — blocking full orchestration endpoint | Done |
| `POST /api/agents/run/stream` — SSE streaming endpoint (one event per agent) | Done |
| `GET /api/agents/` — list all agents with metadata | Done |
| `GET /api/agents/{name}/info` — single agent info | Done |
| Outreach draft generation service | Pending |

**Live test result** (AI/ML conference, Bengaluru, 500 attendees):
- Wave 1 (parallel): sponsor ✓, speaker ✓, venue ✓, exhibitor ✓
- Wave 2 (sequential): pricing ✓ (₹10.25L projected), ops ✓, gtm ✓
- Total time: ~37 seconds end-to-end

---

## Phase 3: Frontend [IN PROGRESS — UI shell exists, needs API wiring]

> Frontend shell (Next.js + Tailwind + shadcn/ui) is built with mock data.
> Next step: replace mock data with real API calls.

| Task | Status |
|------|--------|
| Next.js project setup (Tailwind + shadcn/ui) | Done |
| Landing page | Done |
| Event configuration wizard (4-step form) | Done |
| Agent collaboration visualization | Done |
| Agent results panels (sponsors, speakers, venues, pricing, GTM, ops) | Done (mock data) |
| Simulation dashboard (pricing sliders, break-even chart) | Done (mock data) |
| Outreach center (view/edit AI-generated drafts) | Done (mock data) |
| Dataset explorer page | Done (mock data) |
| WebSocket integration for real-time agent updates | Pending |
| Wire `/api/agents/run/stream` → frontend agent pipeline view | Pending |
| Wire `/api/datasets/*` → dataset explorer | Pending |
| Wire agent result panels to real API responses | Pending |
| Connect `/api/events/configure` → orchestrator | Pending |

---

## Phase 4: Integration + Polish [PENDING]

| Task | Status |
|------|--------|
| Connect frontend to backend API (replace all mock data) | Pending |
| End-to-end testing (wizard → agents → results → simulation) | Pending |
| Simulation engine (what-if, break-even, revenue projection) | Pending |
| Outreach draft generation service | Pending |
| Deploy frontend to Vercel | Pending |
| Redeploy backend to Railway with all agents + new routes | Pending |
| Record demo video (3-5 min) | Pending |
| Write ENGINEERING_DOCS.md | Pending |
| Final repo cleanup + README update | Pending |

---

## Tech Stack Summary

| Component | Technology | Status |
|-----------|-----------|--------|
| LLM | Groq (Llama 3.3 70B + Llama 3.1 8B) | Live |
| Live web search | Exa API (neural search) | Live |
| On-demand scraping | crawl4ai + Playwright | Live |
| Backend | FastAPI (Python) on Railway | Live |
| Frontend | Next.js + Tailwind + shadcn/ui | Shell built, needs wiring |
| Database | Supabase (PostgreSQL) | Live — 241 events seeded |
| Vector DB | Pinecone (1024 dims, multilingual-e5-large) | Live — 241 vectors |
| Cache | Upstash Redis | Live |
| Embeddings | Pinecone hosted (multilingual-e5-large) | Live |

## Knowledge Architecture (3 Tiers)

| Tier | Layer | Tech | When |
|------|-------|------|------|
| 1 | Static RAG | Pinecone (semantic) + Supabase (SQL) | Historical grounding — every agent starts here |
| 2 | Live tools | Exa neural search + crawl4ai scraper | Current verification — LLM calls on demand |
| 3 | Memory | Shared state dict passed between waves | Session state, Wave 2 agents use Wave 1 outputs |

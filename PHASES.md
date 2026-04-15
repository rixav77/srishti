# Srishti - Implementation Phases

> Each phase has clear deliverables. Team members can work on independent tracks in parallel.

---

## Phase 0: Project Setup [COMPLETED]

| Task | Status |
|------|--------|
| GitHub repo created | Done |
| Backend scaffolding (FastAPI + routes + models) | Done |
| Domain profiles (conference, music_festival, sporting_event YAML) | Done |
| Environment variables configured (Groq, Supabase, Pinecone, Redis) | Done |
| Backend deployed on Railway | Done |
| Health check working | Done |

**Live URL:** https://srishti-production.up.railway.app

---

## Phase 1: Data Foundation [CURRENT]

### Phase 1A: Mandatory Dataset Collection
> **Can work independently. No backend needed.**

| Task | Owner | Status |
|------|-------|--------|
| Scrape 100+ tech conferences (2025-2026) from conf.tech, Eventbrite, 10times | | Pending |
| Scrape 60+ music festivals (2025-2026) from Songkick, JamBase, Wikipedia | | Pending |
| Scrape 60+ sporting events (2025-2026) from ESPN, Wikipedia | | Pending |
| Normalize + deduplicate all data | | Pending |
| Export `data/conferences_2025_2026.csv` + `.json` | | Pending |
| Export `data/music_festivals_2025_2026.csv` + `.json` | | Pending |
| Export `data/sporting_events_2025_2026.csv` + `.json` | | Pending |
| Write `data/DATA_SOURCES.md` | | Pending |

**Required fields per event:**
- event_name, dates (start/end), location (city/country), category/theme
- sponsors (if known), speakers (if applicable), estimated_attendance
- ticket_price (min/max/currency), website_url
- data_source, extraction_method

**Minimum:** 50 events per domain, 220+ total

### Phase 1B: Database + Vector DB Setup
> **Can work independently. Needs env vars.**

| Task | Owner | Status |
|------|-------|--------|
| Create Supabase tables (events, sponsors, talents, venues, communities) | | Pending |
| Build `backend/app/data/database.py` connection module | | Pending |
| Build `backend/app/services/embedding.py` (HuggingFace API) | | Pending |
| Seed database with mandatory dataset | | Pending |
| Generate embeddings and load into Pinecone | | Pending |
| Add `/api/datasets/stats` endpoint | | Pending |
| Add `/api/search` endpoint (vector search test) | | Pending |

### Phase 1C: Verify Data Pipeline
| Task | Owner | Status |
|------|-------|--------|
| Test vector search returns relevant results | | Pending |
| Test DB queries return correct data | | Pending |
| Redeploy to Railway with data layer | | Pending |

---

## Phase 1.5: Live Tools Layer [NEW]

> Addresses the "static RAG" gap: agents can now fetch current info on demand.
> Without this, agents only know what was scraped — no freshness.

| Task | Owner | Status |
|------|-------|--------|
| Sign up for Exa API + add `EXA_API_KEY` to env | | Pending |
| Build `backend/app/services/tools.py` with `search_web(query)` via Exa | | Pending |
| Add Redis caching wrapper (`cached_web_search` with 1h TTL) | | Pending |
| Add `scrape_page(url)` tool using Playwright for on-demand scraping | | Pending |
| Define tool schemas in Groq function-calling format | | Pending |
| Test tool-calling loop: LLM → tool → result → LLM (ReAct pattern) | | Pending |
| Document tool list + when each agent should call them | | Pending |

**Tool inventory (target):**

| Tool | Purpose | Used by |
|------|---------|---------|
| `search_web(query)` | General web search (Exa/Tavily) | Any agent |
| `scrape_page(url)` | Fetch + parse arbitrary page (Playwright) | Any agent |
| `get_company_info(name)` | Crunchbase/LinkedIn lookup | Sponsor, Exhibitor |
| `get_artist_stats(name)` | Spotify monthly listeners (music domain) | Speaker/Artist |
| `check_venue_availability(venue, date)` | Live venue API | Venue |

---

## Phase 2: AI Agents [NEXT]

> Every agent now uses BOTH Tier 1 RAG (Pinecone + Supabase) AND Tier 2 live tools (Exa/Playwright).
> Pattern: RAG first for historical grounding, then call tools for current verification.

### Phase 2A: Core Agents (Wave 1 - Independent)
> **Can work in parallel. Each agent is a separate file.**

| Task | Owner | Status |
|------|-------|--------|
| Sponsor Agent (`backend/app/agents/sponsor_agent.py`) — RAG + `search_web` tool | | Pending |
| Speaker/Artist Agent (`backend/app/agents/speaker_agent.py`) — RAG + `get_artist_stats` | | Pending |
| Exhibitor Agent (`backend/app/agents/exhibitor_agent.py`) — RAG + `get_company_info` | | Pending |
| Venue Agent (`backend/app/agents/venue_agent.py`) — RAG + `check_venue_availability` | | Pending |

### Phase 2B: Dependent Agents (Wave 2-3)
> **Depends on Phase 2A outputs.**

| Task | Owner | Status |
|------|-------|--------|
| Pricing & Footfall Agent (`backend/app/agents/pricing_agent.py`) | | Pending |
| Community & GTM Agent (`backend/app/agents/gtm_agent.py`) | | Pending |
| Event Ops Agent (`backend/app/agents/ops_agent.py`) | | Pending |

### Phase 2C: Orchestration
> **Depends on all agents.**

| Task | Owner | Status |
|------|-------|--------|
| LangGraph orchestrator (`backend/app/agents/orchestrator.py`) | | Pending |
| Wave-based parallel execution | | Pending |
| WebSocket streaming to frontend | | Pending |
| Outreach draft generation service | | Pending |

---

## Phase 3: Frontend [CAN START IN PARALLEL WITH PHASE 2]

| Task | Owner | Status |
|------|-------|--------|
| Next.js project setup (Tailwind + shadcn/ui) | | Pending |
| Landing page | | Pending |
| Event configuration wizard (4-step form) | | Pending |
| Agent collaboration visualization (React Flow) | | Pending |
| Agent results panels (sponsors, speakers, venues, etc.) | | Pending |
| Simulation dashboard (pricing sliders, break-even chart) | | Pending |
| Outreach center (view/edit AI-generated drafts) | | Pending |
| Dataset explorer page | | Pending |
| WebSocket integration for real-time agent updates | | Pending |

---

## Phase 4: Integration + Polish [FINAL]

| Task | Owner | Status |
|------|-------|--------|
| Connect frontend to backend API | | Pending |
| End-to-end testing (wizard → agents → results → simulation) | | Pending |
| ML models: pricing prediction, attendance forecasting | | Pending |
| Simulation engine (what-if, break-even, revenue projection) | | Pending |
| Deploy frontend to Vercel | | Pending |
| Redeploy backend with all agents | | Pending |
| Record demo video (3-5 min) | | Pending |
| Write ENGINEERING_DOCS.md | | Pending |
| Final repo cleanup + README update | | Pending |

---

## Tech Stack Summary

| Component | Technology | Cost |
|-----------|-----------|------|
| LLM | Groq (Llama 3.3 70B + Llama 3.1 8B) | Free |
| Embeddings | HuggingFace Inference API (BGE-M3) | Free |
| **Live web search (tools)** | **Exa API + Tavily** | **Free tier** |
| **On-demand scraping (tools)** | **Playwright / crawl4ai** | **Free** |
| Backend | FastAPI (Python) | Free (Railway) |
| Frontend | Vite + React + shadcn/ui | Free (Vercel) |
| Database | Supabase (PostgreSQL) | Free |
| Vector DB | Pinecone (Starter) | Free |
| Cache | Upstash Redis | Free |
| Orchestration | LangGraph | - |

## Knowledge Architecture (3 Tiers)

| Tier | Layer | Tech | When |
|------|-------|------|------|
| 1 | Static RAG | Pinecone (semantic) + Supabase (SQL) | Historical grounding, every agent starts here |
| 2 | Live tools | Exa / Tavily / Playwright | Current verification, called by LLM when needed |
| 3 | Memory | LangGraph checkpoints | Session state, user prefs |

---



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

## Phase 2: AI Agents [NEXT]

### Phase 2A: Core Agents (Wave 1 - Independent)
> **Can work in parallel. Each agent is a separate file.**

| Task | Owner | Status |
|------|-------|--------|
| Sponsor Agent (`backend/app/agents/sponsor_agent.py`) | | Pending |
| Speaker/Artist Agent (`backend/app/agents/speaker_agent.py`) | | Pending |
| Exhibitor Agent (`backend/app/agents/exhibitor_agent.py`) | | Pending |
| Venue Agent (`backend/app/agents/venue_agent.py`) | | Pending |

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
| LLM | Groq (Llama 3.3 70B) | Free |
| Embeddings | HuggingFace Inference API (BGE-M3) | Free |
| Backend | FastAPI (Python) | Free (Railway) |
| Frontend | Next.js 14 + Tailwind + shadcn/ui | Free (Vercel) |
| Database | Supabase (PostgreSQL) | Free |
| Vector DB | Pinecone (Starter) | Free |
| Cache | Upstash Redis | Free |
| Orchestration | LangGraph | - |

---

## How to Work in Parallel

```
Person A (Data)     → Phase 1A (scraping scripts + dataset)
Person B (Backend)  → Phase 1B (DB tables + Pinecone)
Person C (Backend)  → Phase 2A agents (sponsor + speaker)
Person D (Backend)  → Phase 2A agents (venue + exhibitor)
Person E (Frontend) → Phase 3 (Next.js setup + wizard + dashboard)
```

Each person clones the repo, works on their files, and pushes to a feature branch.
Merge to main when ready.

# Srishti — Project Status

> Last updated: 2026-04-16

---

## TL;DR

Backend is fully functional end-to-end. All 7 AI agents are built and tested.
Data is live in Supabase + Pinecone. Frontend shell exists but is running on mock data.
**Next critical task: wire frontend to the real API.**

---

## What's Live Right Now

| Layer | Status | Details |
|-------|--------|---------|
| Backend API | ✅ Live on Railway | `https://srishti-production.up.railway.app` |
| Database | ✅ Live on Supabase | 241 events, 165 sponsors, 240 talents, 159 venues |
| Vector DB | ✅ Live on Pinecone | 241 embeddings, namespace "events", 1024 dims |
| AI Agents | ✅ All 7 built + tested | Sponsor, Speaker, Venue, Exhibitor, Pricing, GTM, Ops |
| Live Tools | ✅ Working | Exa search, crawl4ai scraper, Redis cache |
| Data pipeline | ✅ Working | 4 scrapers (Devfolio, District, Mepass, Skillboxes) |
| Frontend | ⚠️ Shell only | UI exists, running on mock data — not wired to API |

---

## Data

### Events Dataset
| Domain | Count | Sources |
|--------|-------|---------|
| Conferences / Hackathons | 88 | Devfolio, District, Mepass + curated |
| Music Festivals / Concerts | 130 | District, Skillboxes, Mepass + curated |
| Sporting Events | 23 | District + curated (IPL, FIFA WC, Wimbledon, etc.) |
| **Total** | **241** | 4 scrapers + Exa web research |

### Coverage
- Countries: 9 (India, USA, UK, Germany, France, Japan, Brazil, UAE, Australia)
- Cities: 55 unique
- Sponsors: 165 unique companies, 369 event links
- Talents: 240 unique speakers/artists/athletes, 270 event links
- Venues: 159 unique, extracted from events
- Price coverage: 213/241 events have ticket pricing
- Attendance: 100% coverage

---

## API Endpoints

### Datasets (live, hitting Supabase)
| Endpoint | Description |
|----------|-------------|
| `GET /api/datasets/stats` | Counts by domain, year, unique cities/countries |
| `GET /api/datasets/events` | Paginated list with domain/city/country/year filters |
| `GET /api/datasets/events/{id}` | Full event detail with sponsors + talents |
| `GET /api/datasets/search?q=...` | Keyword search across name/description/category/venue |
| `GET /api/datasets/sponsors` | Sponsor list with industry/country filters |
| `GET /api/datasets/talents` | Talent list with type filter (speaker/artist/athlete) |
| `GET /api/datasets/venues` | Venue list with city/capacity filters |

### Agents (live, hitting Groq + Exa + Supabase)
| Endpoint | Description |
|----------|-------------|
| `POST /api/agents/run` | Run all 7 agents, blocking, returns full plan |
| `POST /api/agents/run/stream` | SSE stream — one JSON event per agent as it completes |
| `GET /api/agents/` | List all agents with metadata |
| `GET /api/agents/{name}/info` | Single agent info |

### Health
| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | `{"status": "healthy"}` |

---

## Agent Architecture

```
POST /api/agents/run  (EventConfig)
         │
         ▼
    Orchestrator
         │
    ┌────┴────────────────────────────┐
    │         Wave 1 (parallel)       │
    │  Sponsor  Speaker  Venue  Exhibitor
    └────┬────────────────────────────┘
         │  shared_state passed down
    ┌────┴──────────────────┐
    │    Wave 2 (sequential) │
    │  Pricing → Ops → GTM  │
    └────┬──────────────────┘
         │
    ConsolidatedPlan (JSON)
```

Each agent flow:
1. **Tier 1 RAG** — SQL query on Supabase for similar past events
2. **Tier 2 Tools** — Groq LLM calls `search_web` / `get_company_info` / `get_artist_stats` via ReAct loop
3. Returns ranked JSON list (sponsors / talents / venues / etc.)

---

## File Structure (key files)

```
backend/app/
├── config.py                    # Settings, .env loader
├── data/
│   ├── database.py              # Supabase client facade (get_events, search, stats)
│   └── models.py                # Pydantic models (EventConfig, AgentOutput, etc.)
├── services/
│   └── tools.py                 # Live tools: search_web, scrape_page, get_company_info, get_artist_stats
├── agents/
│   ├── base_agent.py            # Abstract BaseAgent (run, execute, score_candidates)
│   ├── orchestrator.py          # Wave-based orchestrator + SSE streaming
│   ├── sponsor_agent.py         # Wave 1
│   ├── speaker_agent.py         # Wave 1 (domain-aware: speaker/artist/athlete)
│   ├── venue_agent.py           # Wave 1
│   ├── exhibitor_agent.py       # Wave 1
│   ├── pricing_agent.py         # Wave 2
│   ├── ops_agent.py             # Wave 2
│   └── gtm_agent.py             # Wave 2
├── api/routes/
│   ├── agents.py                # POST /run, POST /run/stream, GET /
│   ├── data.py                  # GET /stats, /events, /search, /sponsors, /talents, /venues
│   └── events.py                # POST /configure (triggers orchestrator)
└── scrapers/
    ├── pipeline.py              # ETL orchestration
    ├── normalize.py             # Unified schema normalization + classify_event()
    └── india/
        ├── devfolio.py          # Hackathon scraper (httpx + __NEXT_DATA__)
        ├── district.py          # Pan-India events (crawl4ai + JSON-LD)
        ├── mepass.py            # Indian ticketing (crawl4ai + markdown)
        └── skillboxes.py        # Music events (crawl4ai + markdown)

scripts/
├── sql/01_schema.sql            # Full Supabase schema (run once)
├── seed_supabase.py             # Seeds all 241 events + sponsors/talents/venues
└── seed_pinecone.py             # Seeds 241 event vectors into Pinecone

data/
├── conferences_2025_2026.json   # 88 events
├── music_festivals_2025_2026.json # 130 events
├── sporting_events_2025_2026.json # 23 events
└── DATA_SOURCES.md              # Source documentation
```

---

## What's Pending

### High Priority (blocks demo)
1. **Wire frontend to backend API** — replace mock data in all agent result panels
2. **SSE/WebSocket integration** — connect `POST /api/agents/run/stream` to frontend pipeline view
3. **Redeploy backend to Railway** — new routes (agents, datasets) not yet deployed

### Medium Priority
4. **Outreach draft generation** — LLM-generated email drafts for sponsors/speakers
5. **Simulation engine** — what-if pricing sliders, break-even chart (currently static mock)

### Low Priority / Nice-to-have
6. Semantic vector search endpoint (Pinecone → Supabase join)
7. BookMyShow scraper (blocked by Cloudflare — needs residential proxy or API)
8. `embedding.py` service (HuggingFace) — Pinecone's hosted model used instead, so lower priority
9. Engineering docs

---

## Known Issues

| Issue | Impact | Fix |
|-------|--------|-----|
| Groq free tier 100k TPD limit | Agent calls fail if daily quota exhausted | Use `fast_model` (8B) for tool calls, `default_model` (70B) for final answer |
| `scrape_page` can't be called from async context | Falls back to empty string | Fixed with ThreadPoolExecutor; works reliably now |
| Exhibitor agent sometimes hits token limit mid-run | Returns empty list | Will resolve at lower daily usage; add retry logic |
| Redis URL needs `rediss://` for TLS | Caching disabled locally | Upstash URL works on Railway with correct scheme |
| BookMyShow blocked by Cloudflare | No BMS events in dataset | Removed from pipeline; can revisit with proxy |

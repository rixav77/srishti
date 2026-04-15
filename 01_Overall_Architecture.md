# 01 — Overall System Architecture

## 1.1 Project Name: **Srishti** (Sanskrit: "Creation")

An AI-powered multi-agent event intelligence platform that autonomously plans, optimizes, and executes conferences, music festivals, and sporting events.

---

## 1.2 Domain-Agnostic Design (Extra Points Strategy)

The system is built **domain-agnostic from day one**. Rather than hardcoding for "conferences," we use an **Event Domain Abstraction Layer**:

```
┌─────────────────────────────────────────────────┐
│              Domain Configuration                │
├─────────────────────────────────────────────────┤
│  domain: "conference" | "music_festival" |       │
│          "sporting_event" | "custom"             │
│                                                  │
│  entity_mappings:                                │
│    performer: "speaker" | "artist" | "athlete"   │
│    exhibitor: "exhibitor" | "vendor" | "sponsor" │
│    venue_type: "convention" | "arena" | "stadium"│
│    ticket_tiers: domain-specific defaults        │
│    community_channels: domain-specific defaults  │
│                                                  │
│  scoring_weights: domain-specific relevance      │
│  data_sources: domain-specific scrapers          │
└─────────────────────────────────────────────────┘
```

Each agent reads from this config. When a user selects "Music Festival," the Speaker Agent becomes an "Artist Agent," venue search filters shift to outdoor/arena types, pricing models switch to festival economics, and community channels target music-specific platforms.

**How this works in practice:**
- A `DomainConfig` object is injected into every agent at initialization
- Agent prompts, tool selections, and scoring weights adapt based on domain
- The data layer has unified schemas with domain-specific optional fields
- The UI dynamically relabels and reshapes based on selected domain

---

## 1.3 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌──────────────────┐  │
│  │  Event    │ │ Agent    │ │ Simulation │ │ Collaboration    │  │
│  │  Wizard   │ │ Dashboard│ │ Dashboard  │ │ Visualizer       │  │
│  └────┬─────┘ └────┬─────┘ └─────┬──────┘ └───────┬──────────┘  │
│       └─────────────┴─────────────┴────────────────┘             │
│                           │ WebSocket + REST                     │
└───────────────────────────┼──────────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────────┐
│                    API GATEWAY (FastAPI)                          │
│              /events  /agents  /simulate  /data  /ws             │
└───────────────────────────┼──────────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────────┐
│                ORCHESTRATION LAYER (LangGraph)                   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │              Multi-Agent Supervisor                      │     │
│  │    (routes tasks, manages state, resolves conflicts)     │     │
│  └──┬──────┬──────┬──────┬──────┬──────┬──────┬────────────┘     │
│     │      │      │      │      │      │      │                  │
│  ┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐             │
│  │Spnsr││Spkr ││Exhbt││Venue││Price││GTM  ││Ops  │             │
│  │Agent││Agent││Agent││Agent││Agent││Agent││Agent│             │
│  └──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘             │
│     └──────┴──────┴──────┴──────┴──────┴──────┘                 │
│                    Shared State (LangGraph)                       │
│                    + Vector Memory (Pinecone)                     │
└───────────────────────────┼──────────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────────┐
│                    KNOWLEDGE LAYER (3 Tiers)                      │
│                                                                  │
│  Tier 1: STATIC (scraped + curated, fast + frozen)               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                 │
│  │ Supabase    │  │ Pinecone   │  │ Redis      │                 │
│  │ (Postgres)  │  │ (vector    │  │ (cache +   │                 │
│  │ structured  │  │ embeddings │  │ sessions)  │                 │
│  │ events,     │  │ for RAG    │  │            │                 │
│  │ sponsors    │  │ memory)    │  │            │                 │
│  └────────────┘  └────────────┘  └────────────┘                 │
│                                                                  │
│  Tier 2: LIVE TOOLS (agent-callable, fresh)                      │
│  ┌────────────────────────────────────────────┐                  │
│  │  Exa / Tavily  │ Playwright │ Live APIs    │                  │
│  │  (web search)  │ (on-demand │ (Crunchbase, │                  │
│  │                │  scraping) │  LinkedIn)   │                  │
│  └────────────────────────────────────────────┘                  │
│  LLMs invoke these via function-calling when they need           │
│  current info not present in Tier 1.                             │
│                                                                  │
│  Tier 3: DATA AGGREGATION (batch/offline)                        │
│  ┌────────────────────────────────────────────┐                  │
│  │  Scrapers │ APIs │ CSV/JSON Ingest │ ETL    │                  │
│  │  Runs nightly/weekly to refresh Tier 1     │                  │
│  └────────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1.4 Core Architectural Principles

| Principle | Implementation |
|-----------|---------------|
| **Domain-agnostic** | `DomainConfig` abstraction; every agent parameterized by domain |
| **Agent autonomy** | Each agent is a self-contained LangGraph node with own tools and memory |
| **Shared context** | LangGraph shared state + Pinecone vector store for cross-agent memory |
| **Hybrid knowledge** | Static RAG (historical) + Live tools (current) — agents pick the right layer per query |
| **Data-first** | All recommendations backed by real scraped/aggregated data + live verification |
| **Simulation-ready** | Every numerical output feeds into what-if scenario engine |
| **Extensible** | New agents plug in via standard interface; new domains via config |

---

## 1.5 Data Flow Summary

```
User Input (event details: type, theme, budget, location, date, audience size)
    │
    ▼
Orchestrator decomposes into sub-tasks
    │
    ├──▶ Sponsor Agent ──▶ ranked sponsor list + outreach drafts
    ├──▶ Speaker Agent ──▶ ranked speaker list + outreach drafts
    ├──▶ Exhibitor Agent ──▶ categorized exhibitor recommendations
    ├──▶ Venue Agent ──▶ ranked venue options with comparisons
    ├──▶ Pricing Agent ──▶ pricing model + footfall prediction
    ├──▶ GTM Agent ──▶ community targets + messaging strategy
    └──▶ Ops Agent ──▶ schedule + resource plan + conflict resolution
    │
    ▼
Agents share intermediate results (e.g., Venue choice affects Pricing model)
    │
    ▼
Consolidated Event Plan (structured JSON + visual dashboard)
    │
    ▼
Simulation layer allows what-if adjustments
    │
    ▼
Export: PDF report, outreach emails, CSV data, shareable dashboard
```

---

## 1.6 Deployment Topology

| Component | Service | Hosting |
|-----------|---------|---------|
| Frontend | Vite + React + shadcn/ui | Vercel |
| API | FastAPI | Railway |
| Orchestration | LangGraph (Python) | Same as API |
| Database | Supabase (PostgreSQL) | Supabase Cloud (free) |
| Vector DB | Pinecone | Pinecone Cloud (free tier) |
| Cache | Upstash Redis | Upstash (free) |
| Scrapers | Playwright / crawl4ai | Run offline to seed Tier 1 |
| **LLM** | **Groq — Llama 3.3 70B** | Free, ultra-fast inference |
| **Embeddings** | **BGE-M3 via HuggingFace API** | Free, 1024 dims |
| **Live search tools** | **Exa API / Tavily** | Free tier |

All services have free tiers sufficient for a hackathon prototype.

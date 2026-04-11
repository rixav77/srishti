# 08 - Deliverables & Timeline

---

## 1. Final Deliverables Checklist (from PDF)

| # | Deliverable | Format | Status Plan |
|---|------------|--------|-------------|
| 1 | GitHub repository with complete source code | Public repo | Phase 4 |
| 2 | Hosted platform / working prototype | Vercel + Railway URLs | Phase 4 |
| 3 | Short demo video showcasing the system | 3-5 min video | Phase 5 |
| 4 | Engineering document explaining architecture and agent logic | Markdown in repo + PDF | Phase 5 |
| 5 | Sources of data | DATA_SOURCES.md + inline citations | Phase 2-3 |
| 6 | Mandatory structured dataset (CSV/JSON) | `data/` directory | Phase 2 |

---

## 2. Phased Task Breakdown

### Phase 0: Setup (Day 0 - 4 hours)

| Task | Owner | Time | Priority |
|------|-------|------|----------|
| Create GitHub repo with project structure | All | 30m | P0 |
| Set up backend (FastAPI + pyproject.toml) | Backend | 1h | P0 |
| Set up frontend (Next.js + Tailwind + shadcn) | Frontend | 1h | P0 |
| Create Supabase project + database schema | Backend | 1h | P0 |
| Create Pinecone index + test connection | Backend | 30m | P0 |
| Set up Upstash Redis | Backend | 15m | P0 |
| Configure environment variables (.env) | All | 15m | P0 |
| Set up CI (GitHub Actions: lint + type check) | Any | 30m | P1 |

**Exit criteria**: `uvicorn` serves a health check; `npm run dev` shows Next.js app; DB connected.

---

### Phase 1: Data Foundation (Day 1 - 8 hours)

| Task | Owner | Time | Priority | Dependencies |
|------|-------|------|----------|-------------|
| Build base scraper class | Backend | 1h | P0 | Phase 0 |
| Implement conf.tech scraper | Backend | 1.5h | P0 | Base scraper |
| Implement Eventbrite API integration | Backend | 1.5h | P0 | Base scraper |
| Implement Songkick/Bandsintown API | Backend | 1h | P1 | Base scraper |
| Implement sports event scraper (ESPN) | Backend | 1h | P1 | Base scraper |
| Manual data curation (fill gaps) | PM/Data | 3h | P0 | Scrapers running |
| Data normalization + dedup pipeline | Backend | 1.5h | P0 | Raw data collected |
| Generate CSV/JSON mandatory deliverable | Backend | 1h | P0 | Normalized data |
| Write DATA_SOURCES.md | PM | 1h | P0 | All data collected |
| Seed PostgreSQL with mandatory dataset | Backend | 30m | P0 | CSV/JSON ready |
| Generate embeddings + load Pinecone | Backend | 1h | P0 | Data in PostgreSQL |

**Exit criteria**: 220+ events in DB, CSV/JSON exported, Pinecone loaded, DATA_SOURCES.md complete.

---

### Phase 2: Agent Core (Day 2-3 - 16 hours)

| Task | Owner | Time | Priority | Dependencies |
|------|-------|------|----------|-------------|
| Implement BaseAgent interface | Backend | 1h | P0 | Phase 1 |
| Implement DomainConfig system | Backend | 1.5h | P0 | Phase 0 |
| Build multi-dimensional scoring framework | Backend | 1.5h | P0 | BaseAgent |
| **Sponsor Agent** - full implementation | Backend | 2.5h | P0 | Scoring framework |
| **Speaker/Artist Agent** - full implementation | Backend | 2.5h | P0 | Scoring framework |
| **Venue Agent** - full implementation | Backend | 2h | P0 | Scoring framework |
| **Exhibitor Agent** - full implementation | Backend | 2h | P0 | Scoring framework |
| **Pricing & Footfall Agent** - full implementation | Backend | 3h | P0 | Venue + Speaker agents |
| **Community & GTM Agent** - full implementation | Backend | 2h | P0 | Speaker agent |
| **Event Ops Agent** - full implementation | Backend | 2.5h | P1 | All above agents |
| Outreach draft generation service | Backend | 1.5h | P0 | Sponsor + Speaker agents |
| RAG pipeline (vector search + SQL enrichment) | Backend | 2h | P0 | Pinecone loaded |

**Exit criteria**: All 7 agents return structured output for a test event. Outreach drafts generated.

---

### Phase 3: Orchestration + API (Day 3-4 - 10 hours)

| Task | Owner | Time | Priority | Dependencies |
|------|-------|------|----------|-------------|
| Build LangGraph orchestrator (supervisor pattern) | Backend | 3h | P0 | All agents |
| Implement wave-based execution (parallel + sequential) | Backend | 2h | P0 | Orchestrator |
| WebSocket streaming (agent progress events) | Backend | 2h | P0 | Orchestrator |
| REST API routes (/events, /agents, /simulate, /data) | Backend | 2h | P0 | Orchestrator |
| Error handling + retry logic | Backend | 1h | P0 | API routes |
| Simulation engine (pricing, break-even, what-if) | Backend | 2h | P0 | Pricing agent |
| End-to-end test: full pipeline from input to plan | Backend | 1h | P0 | All above |

**Exit criteria**: POST /events/configure triggers all agents, results stream via WebSocket, full plan returned.

---

### Phase 4: Frontend (Day 4-5 - 14 hours)

| Task | Owner | Time | Priority | Dependencies |
|------|-------|------|----------|-------------|
| Landing page | Frontend | 1.5h | P1 | — |
| Event configuration wizard (4-step form) | Frontend | 3h | P0 | API routes |
| Agent collaboration visualization (React Flow) | Frontend | 3h | P0 | WebSocket streaming |
| Agent results panels (sponsors, speakers, etc.) | Frontend | 3h | P0 | API routes |
| Simulation dashboard (sliders, charts, scenarios) | Frontend | 3h | P0 | Simulation engine |
| Outreach center (view/edit drafts) | Frontend | 1.5h | P1 | Outreach API |
| Dataset explorer page | Frontend | 1h | P1 | Data API |
| Real-time WebSocket integration | Frontend | 1h | P0 | WebSocket API |
| Polish: loading states, animations, responsiveness | Frontend | 2h | P1 | All above |

**Exit criteria**: Full user flow works: wizard → agents run → dashboard shows results → simulation works.

---

### Phase 5: Polish & Deliverables (Day 5-6 - 8 hours)

| Task | Owner | Time | Priority | Dependencies |
|------|-------|------|----------|-------------|
| Deploy backend to Railway/Render | Backend | 1h | P0 | Phase 3 |
| Deploy frontend to Vercel | Frontend | 30m | P0 | Phase 4 |
| End-to-end testing on deployed version | All | 1h | P0 | Both deployed |
| Record demo video (3-5 minutes) | PM | 2h | P0 | Working prototype |
| Write ARCHITECTURE.md (engineering doc) | Backend | 1.5h | P0 | — |
| Write AGENT_DESIGN.md | Backend | 1h | P0 | — |
| Write API_REFERENCE.md | Backend | 30m | P1 | — |
| README.md with setup instructions | All | 30m | P0 | — |
| Final repo cleanup + last commit | All | 30m | P0 | All above |

**Exit criteria**: All 6 deliverables complete. Demo video recorded. Hosted prototype accessible.

---

## 3. GitHub Repository Structure

```
srishti/
├── README.md                    # Project overview + setup + demo link
├── ENGINEERING_DOCS.md          # Complete architecture + agent logic document
├── LICENSE                      # MIT
├── .env.example
├── docker-compose.yml           # Optional: local dev with all services
│
├── backend/                     # (see 06_Tech_Stack.md for full tree)
├── frontend/                    # (see 06_Tech_Stack.md for full tree)
│
├── data/                        # MANDATORY DELIVERABLE
│   ├── conferences_2025_2026.csv
│   ├── conferences_2025_2026.json
│   ├── music_festivals_2025_2026.csv
│   ├── music_festivals_2025_2026.json
│   ├── sporting_events_2025_2026.csv
│   ├── sporting_events_2025_2026.json
│   ├── DATA_SOURCES.md          # Source documentation
│   └── scripts/                 # Scraping/collection scripts
│
├── domain_profiles/             # Domain-agnostic config
│   ├── conference.yaml
│   ├── music_festival.yaml
│   └── sporting_event.yaml
│
├── docs/                        # Additional engineering docs
│   ├── ARCHITECTURE.md
│   ├── AGENT_DESIGN.md
│   ├── DATA_PIPELINE.md
│   ├── API_REFERENCE.md
│   └── DEMO_SCRIPT.md
│
└── demo/                        # Demo assets
    ├── screenshots/
    └── demo_video_link.md
```

---

## 4. Demo Video Script (3-5 minutes)

### Outline

```
0:00 - 0:20  │ Opening: Problem statement (data fragmentation in event planning)
0:20 - 0:40  │ Solution overview: Srishti - AI multi-agent event intelligence
0:40 - 1:00  │ Architecture diagram: 7 agents + orchestration + data layer
1:00 - 1:30  │ LIVE DEMO: Event configuration wizard (select AI Conference, India, 2000 ppl)
1:30 - 2:30  │ LIVE DEMO: Agents working in real-time (collaboration graph + activity log)
2:30 - 3:00  │ LIVE DEMO: Results - sponsor list, speaker list, venue recommendations
3:00 - 3:30  │ LIVE DEMO: Simulation dashboard (adjust pricing, see break-even)
3:30 - 3:50  │ LIVE DEMO: Outreach drafts (personalized email for top sponsor)
3:50 - 4:10  │ Dataset deliverable + domain-agnostic architecture (switch to Music Festival)
4:10 - 4:30  │ Tech stack + engineering highlights (RAG, LangGraph, real-time)
4:30 - 5:00  │ Closing: Impact, extensibility, team
```

### Key Demo Moments (to impress judges)
1. **Real-time agent graph**: Show agents activating, passing data, completing in waves
2. **Context-aware results**: Highlight that sponsors recommended actually match the event
3. **Simulation**: Drag a pricing slider, watch break-even chart update instantly
4. **Domain switch**: Change from "Conference" to "Music Festival" — show the entire system adapts
5. **Outreach draft**: Show a personalized email referencing the sponsor's actual past events

---

## 5. Engineering Document Structure

The ENGINEERING_DOCS.md file covers:

```markdown
# Srishti - Engineering Documentation

## 1. System Overview
   - Problem statement and motivation
   - Architecture diagram
   - Domain-agnostic design philosophy

## 2. Multi-Agent Architecture
   - Agent list and responsibilities
   - Agent interface and scoring framework
   - Inter-agent communication via shared state
   - Wave-based execution strategy

## 3. Orchestration (LangGraph)
   - Graph definition and routing logic
   - Supervisor pattern
   - Checkpointing and memory
   - Error handling and graceful degradation

## 4. Data Pipeline
   - Data sources and collection methodology
   - Scraping pipeline architecture
   - ETL: normalize, deduplicate, validate
   - Vector DB (Pinecone) embedding strategy

## 5. AI/ML Components
   - Recommendation engine (retrieval + scoring + ranking)
   - Predictive modeling (pricing, attendance, conversion)
   - RAG pipeline (vector search + SQL + LLM)
   - Outreach generation (personalized, context-aware)

## 6. Simulation Engine
   - Pricing simulation
   - Break-even analysis
   - Revenue projection
   - What-if scenario framework

## 7. Frontend Architecture
   - Component structure
   - Real-time WebSocket integration
   - Visualization approach (React Flow, Recharts)

## 8. Deployment
   - Hosting topology
   - Environment setup
   - API reference

## 9. Data Deliverable
   - Dataset overview (220+ events)
   - Sources and methodology
   - Quality metrics
```

---

## 6. Timeline Summary

| Day | Focus | Key Output |
|-----|-------|-----------|
| Day 0 | Setup | Project structure, DB, services connected |
| Day 1 | Data | 220+ events collected, CSV/JSON ready, Pinecone loaded |
| Day 2 | Agents (1-4) | Sponsor, Speaker, Venue, Exhibitor agents working |
| Day 3 | Agents (5-7) + Orchestration | Pricing, GTM, Ops agents + LangGraph orchestrator |
| Day 4 | Frontend | Wizard + dashboard + agent visualization |
| Day 5 | Frontend + Simulation | Simulation dashboard + outreach center |
| Day 6 | Polish + Deliverables | Deploy, demo video, engineering docs, final cleanup |

---

## 7. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Scraping blocked/rate-limited | Pre-populate with manual data; cache aggressively |
| LLM API downtime during demo | Cache agent results; fallback to pre-computed demo data |
| Agent takes too long during demo | Set timeouts; have pre-computed backup results |
| Frontend not ready in time | Start with minimal dashboard, add polish iteratively |
| Pinecone free tier limit | Use ChromaDB locally as fallback |
| Team member unavailable | Each phase has clear ownership; docs enable handoff |

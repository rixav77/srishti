# Srishti

Srishti is an AI-powered multi-agent event intelligence platform that autonomously plans and optimizes conferences, hackathons, music festivals, and sporting events. Given a minimal set of event parameters, the system deploys seven specialized AI agents that research sponsors, speakers, venues, exhibitors, pricing strategies, go-to-market plans, and operations checklists simultaneously — returning a consolidated, actionable event plan in under two minutes.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [End-to-End Workflow](#end-to-end-workflow)
- [Agent System](#agent-system)
- [Knowledge Tiers](#knowledge-tiers)
- [Orchestration Model](#orchestration-model)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Technology Stack](#technology-stack)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [Dataset](#dataset)

---

## Overview

Planning a large event requires coordinating dozens of independent workstreams: identifying sponsors aligned with your audience, sourcing credible speakers, selecting a venue that fits your capacity and budget, pricing tickets to maximize revenue without sacrificing attendance, and assembling a go-to-market strategy across the right communities. This work is typically spread across multiple teams over several weeks.

Srishti collapses that process into a single API call. The user specifies the event category, geography, target audience size, and optional budget range. The system's orchestrator dispatches agents across two execution waves, each agent performing real-time web research and database retrieval before reasoning with a large language model to produce ranked, scored recommendations. All seven outputs are merged into a single structured plan returned to the frontend.

---

## Architecture

```
                     ┌──────────────────────────────────────────────────┐
                     │                Frontend (React)                   │
                     │  ProjectsPage  GeneratingPage  ProjectDashboard   │
                     └────────────────────────┬─────────────────────────┘
                                              │ HTTP POST + SSE Stream
                     ┌────────────────────────▼─────────────────────────┐
                     │            FastAPI Backend (Railway)              │
                     │        POST /api/agents/run/stream                │
                     └────────────────────────┬─────────────────────────┘
                                              │
                     ┌────────────────────────▼─────────────────────────┐
                     │                  Orchestrator                     │
                     │                                                   │
                     │  Wave 1 (Parallel)       Wave 2 (Sequential)     │
                     │  SponsorAgent            PricingAgent             │
                     │  SpeakerAgent     ──▶   GTMAgent                 │
                     │  VenueAgent              OpsAgent                 │
                     │  ExhibitorAgent                                   │
                     └────────────────────────┬─────────────────────────┘
                                              │
     ┌────────────────────────────────────────▼────────────────────────────────────────┐
     │                              Knowledge Layer                                     │
     │                                                                                  │
     │   Supabase PostgreSQL         Pinecone Vector DB          Redis Cache            │
     │   241 curated events,         1024-dim embeddings,        1h TTL on             │
     │   sponsors, venues,           semantic similarity          all tool calls        │
     │   talents, junctions          search                                             │
     │                                                                                  │
     │   Exa Neural Search           crawl4ai + Playwright                             │
     │   live web retrieval          on-demand page scraping                            │
     └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## End-to-End Workflow

### Step 1: Define Your Event

The user opens the Projects page and clicks "New Project". The form collects:

| Field | Description |
|---|---|
| Project Name | Optional label for the project |
| Event Category | AI / ML, Web3, Hackathon, FinTech, HealthTech, Gaming, Climate, Music & Arts |
| Geography | One or more regions: North America, Europe, Asia Pacific, Middle East, Latin America |
| City | Optional city for precise venue and speaker targeting |
| Audience Size | Expected total attendance |
| Budget Range | Optional minimum and maximum budget in INR |
| Prize Pool | Hackathon-only: prize pool amount in INR |
| Enable Customization | Allows per-agent instruction injection before the run starts |

### Step 2: Customization (Optional)

If customization is enabled, a pre-flight screen appears before the agents start running. Each of the seven agents has an optional free-text instructions field. These instructions are prepended to the agent's system prompt at runtime. Examples:

- Sponsor agent: "Focus only on fintech companies with India operations. Exclude crypto companies."
- Speaker agent: "Prioritize speakers with conference appearances in the last 12 months."
- Venue agent: "Only consider venues with a dedicated hackathon-style open floor plan."

### Step 3: Agent Execution Begins

On form submission, the frontend sends a POST request to `/api/agents/run/stream` with the event configuration. The backend begins executing agents and streams Server-Sent Events (SSE) back to the browser in real time.

The GeneratingPage consumes the SSE stream using the Fetch API with a ReadableStream decoder — not EventSource, which does not support POST requests. Each SSE event carries:

```json
{
  "wave": 1,
  "agent": "sponsor_agent",
  "status": "complete",
  "results": { "..." },
  "confidence": 0.87,
  "elapsed_ms": 14200
}
```

The UI updates each agent's status card in real time: waiting, running, complete, or error. A progress bar advances as agents finish. The activity log shows a timestamped entry for each state transition.

### Step 4: Wave 1 — Parallel Execution

Four agents run concurrently via `asyncio.gather`. They have no dependencies on each other and begin simultaneously.

**SponsorAgent**

Retrieves historical events from Supabase matching the event's domain and geography. Collects sponsor lists from those events, ranked by frequency of appearance. Passes top candidates to the LLM, which uses `search_web` to verify current India presence, funding status, and budget signals. Returns sponsors ranked by fit with recommended tier (title, gold, silver, bronze), estimated budget range, industry classification, and a brief reasoning statement.

**SpeakerAgent**

Performs semantic search in Pinecone to surface talents matching the event domain and geography. Cross-references results with the `event_talents` table for speakers who have appeared at similar past events. Domain-aware behavior adjusts for the event type: conferences surface keynote, panel, and workshop speakers; music festivals surface headliners, supporting acts, and openers; sporting events surface athletes, coaches, and commentators. Returns speakers with topics, estimated fee range, LinkedIn URL, and follower count.

**VenueAgent**

Queries the Supabase venues table filtered by city and capacity range. Cross-references the `event_venues` junction for venues with relevant prior usage. The LLM uses `search_web` and `scrape_page` to verify current pricing and availability. Returns venues with daily rate estimate, max capacity, venue type (convention center, hotel, stadium, outdoor, arena), amenities list, coordinates, and past events hosted.

**ExhibitorAgent**

Uses the sponsor candidate pool from shared state as its starting company list. Differentiates exhibitors from confirmed sponsors to avoid overlap in recommendations. Classifies each candidate into a category: startup, enterprise, tools, or research. Returns exhibitor candidates with booth tier recommendation (standard, premium, or flagship) and exhibition history.

Wave 1 typically completes in 20–35 seconds. As each agent finishes, the SSE stream emits its result immediately. The frontend shows each agent completing in real time rather than waiting for the group.

### Step 5: Wave 2 — Sequential Execution

Three agents run one after another. Each reads from the shared state populated by Wave 1.

**PricingAgent**

Reads venue max capacity from VenueAgent output to anchor total available ticket inventory. Reads sponsor revenue estimates from SponsorAgent to offset fixed costs. Searches for pricing benchmarks from comparable events in the same domain, geography, and audience size bracket. Constructs three ticket tiers with allocation percentages and projected sales figures. Returns tiers (Early Bird, General, VIP) with prices, projected revenue per tier, total projected revenue, break-even attendee count, expected fill rate, and a sensitivity model for simulation.

**GTMAgent**

Reads confirmed speakers and sponsors from shared state to identify the target audience profile. Searches for communities where those audiences congregate: Discord servers, LinkedIn groups, Reddit subreddits, Slack workspaces, Meetup groups, and WhatsApp communities. Filters by activity level, geographic relevance, and audience alignment. Constructs three strategy phases: Pre-launch (8–6 weeks out), Launch (6–4 weeks), and Push (4 weeks to event day). Returns a community list with membership counts and partnership suggestions, a phase timeline with recommended actions, and a messaging framework with tagline and value propositions.

**OpsAgent**

Reads the speaker list and confirmed session slots from SpeakerAgent. Reads venue room count and layout from VenueAgent. Builds a day-by-day event schedule: each day broken into time slots with assigned speaker, room, track, and session type. Detects scheduling conflicts and resolves them with notes. Generates a resource plan covering staff headcount, AV requirements, catering estimates, and security. Produces a pre-event checklist with tasks, deadlines (in weeks before event), and assigned owners.

Wave 2 typically completes in 15–25 additional seconds.

### Step 6: Consolidation

When all seven agents complete, the orchestrator merges all outputs into a single plan and emits the final SSE event:

```json
{
  "wave": 0,
  "agent": "orchestrator",
  "status": "complete",
  "plan": {
    "config": { "..." },
    "status": "complete",
    "agents": {
      "sponsor_agent":   { "status": "complete", "confidence": 0.87, "elapsed_ms": 14200 },
      "speaker_agent":   { "..." },
      "venue_agent":     { "..." },
      "exhibitor_agent": { "..." },
      "pricing_agent":   { "..." },
      "gtm_agent":       { "..." },
      "ops_agent":       { "..." }
    },
    "sponsors":   [ "..." ],
    "speakers":   [ "..." ],
    "venues":     [ "..." ],
    "exhibitors": [ "..." ],
    "pricing":    { "..." },
    "gtm":        { "..." },
    "ops":        { "..." }
  }
}
```

### Step 7: Results Dashboard

The frontend stores the consolidated plan in React context keyed by project ID. The user is automatically redirected to the Project Dashboard, which exposes the results across seven tabbed pages:

| Tab | Contents |
|---|---|
| Overview | Summary cards across all domains with key metrics |
| Sponsors | Ranked table with tier, match score, budget range, and reasoning |
| Speakers | Table with topic, influence tier (Low / Medium / High / Very High), past talk count |
| Venues | Comparison table with capacity, price per day, star rating, and city |
| Pricing | Tier breakdown with prices, projected revenue, fill rate, and break-even figures |
| GTM | Community list with platform, reach, cost, and priority; three-phase strategy timeline |
| Ops | Day-by-day schedule; pre-event checklist with deadlines; resource plan summary |

---

## Agent System

### Base Agent Pattern

All agents extend `BaseAgent`, which implements a shared ReAct (reason + act) loop:

1. The agent receives a system prompt, the event configuration, and the four available tool schemas
2. The LLM generates a reasoning trace and optionally emits one or more tool calls
3. Tool calls are executed in parallel and their results are appended to the message history
4. The loop repeats for up to 5 rounds
5. When the LLM produces no further tool calls, the final message is parsed as JSON against the agent's output schema
6. If JSON parsing fails, the agent sends a formatting correction prompt and retries once
7. Each result carries a `total_score` (0.0–1.0) composed of sub-scores for relevance, recency, and geographic fit

Groq's function-calling API is used for tool dispatch. The four tool schemas are passed as function definitions, and the model natively selects which tool to call with what arguments.

### SponsorAgent

Input: EventConfig  
Output: List of SponsorResult (company_name, recommended_tier, industry, past_sponsorships, estimated_budget_range, total_score, reasoning, outreach_draft)

### SpeakerAgent

Input: EventConfig  
Output: List of SpeakerResult (name, role, topics, linkedin_url, followers, estimated_fee_range, total_score)

Domain behavior:
- `conference` → roles: keynote, panel, workshop
- `music_festival` → roles: headliner, supporting, opener
- `sporting_event` → roles: athlete, commentator, coach

### VenueAgent

Input: EventConfig  
Output: List of VenueResult (name, city, country, max_capacity, daily_rate_estimate, venue_type, amenities, past_events, coordinates, total_score)

### ExhibitorAgent

Input: EventConfig + shared_state (reads sponsor results)  
Output: List of ExhibitorResult (name, category, booth_tier, exhibition_history, total_score)

### PricingAgent

Input: EventConfig + shared_state (reads venue capacity, sponsor estimates)  
Output: PricingResult (tiers[], total_projected_revenue, break_even_attendees, expected_attendance, fill_rate, confidence_score, sensitivity, break_even)

### GTMAgent

Input: EventConfig + shared_state (reads speaker and sponsor outputs)  
Output: GTMResult (communities[], strategy_phases[], messaging{tagline, value_props, target_personas}, estimated_reach)

### OpsAgent

Input: EventConfig + shared_state (reads speaker schedule, venue details)  
Output: OpsResult (schedule[], conflicts_detected, conflicts_resolved, conflict_notes, resource_plan{}, checklist[])

---

## Knowledge Tiers

Each agent draws from three tiers of knowledge applied in sequence.

### Tier 1 — Curated Historical Database

**Supabase PostgreSQL**

| Table | Description |
|---|---|
| `events` | 241 past events: conferences, festivals, sporting events across 55 cities, 11 countries |
| `sponsors` | Companies with sponsorship history, industry classification, and tier |
| `talents` | Speakers, artists, athletes with domain, country, and social statistics |
| `venues` | Convention centers, stadiums, hotels with capacity and rate data |
| `event_sponsors` | Many-to-many junction: event to sponsor with tier |
| `event_talents` | Many-to-many junction: event to talent with role |
| `event_venues` | Many-to-many junction: event to venue |

**Pinecone Vector Index**

- 1024-dimensional embeddings generated using BAAI/bge-m3 (multilingual)
- Used for semantic similarity search across events and talents
- Enables retrieval of thematically similar events regardless of exact keyword overlap

### Tier 2 — Live Web Research

Four tools are available to all agents at runtime:

| Tool | Implementation | Purpose |
|---|---|---|
| `search_web(query, num_results)` | Exa neural search API | Find current sponsor budgets, speaker recent activity, artist tours, community membership data |
| `scrape_page(url)` | crawl4ai + Playwright headless | Extract full page content from JavaScript-rendered pages; returns clean Markdown |
| `get_company_info(name)` | Exa company search wrapper | Retrieve sponsor or exhibitor industry, HQ location, funding stage, and size |
| `get_artist_stats(name)` | Exa artist/performer search | Retrieve Spotify listeners, genre, recent tour schedule for speakers or artists |

### Tier 3 — Redis Cache

All tool call results are cached in Redis with a one-hour TTL. Repeated calls to the same search query or URL within one hour return the cached result immediately, reducing API cost and latency. When Redis is unavailable (as in serverless cold starts), the tools execute uncached and log a warning.

---

## Orchestration Model

### Wave 1: Parallel Execution

```python
wave1_tasks = [
    asyncio.create_task(sponsor_agent.run(config)),
    asyncio.create_task(speaker_agent.run(config)),
    asyncio.create_task(venue_agent.run(config)),
    asyncio.create_task(exhibitor_agent.run(config)),
]
results = await asyncio.gather(*wave1_tasks, return_exceptions=True)
```

The streaming endpoint uses `asyncio.wait(return_when=FIRST_COMPLETED)` to emit an SSE event as soon as each individual agent finishes, rather than waiting for all four.

### Wave 2: Sequential Execution

```python
for agent in [pricing_agent, gtm_agent, ops_agent]:
    yield running_event(agent.name)
    output = await agent.run(config, shared_state)
    shared_state[agent.name] = output.results
    yield complete_event(agent, output)
```

Sequential execution guarantees that PricingAgent can read VenueAgent's capacity, GTMAgent can read SpeakerAgent's confirmed lineup, and OpsAgent can read both.

### SSE Stream Format

Every event follows the SSE protocol:

```
data: {"wave":1,"agent":"sponsor_agent","status":"complete","results":{...},"confidence":0.87,"elapsed_ms":14200}

data: {"wave":1,"agent":"speaker_agent","status":"error","results":{},"elapsed_ms":41000}

data: {"wave":0,"agent":"orchestrator","status":"complete","plan":{...}}
```

The frontend reads the stream with a manual ReadableStream decoder loop. `EventSource` is not used because the browser's EventSource API does not support POST requests with a request body.

---

## API Reference

### Health

```
GET /api/health
Response: { "status": "healthy", "service": "srishti" }
```

### Agents

```
POST /api/agents/run
```

Runs all seven agents synchronously. Blocks until complete. Returns the consolidated plan as a JSON response body.

```
POST /api/agents/run/stream
```

Runs all seven agents with real-time SSE streaming. Yields one event per agent state change. The final event contains the full consolidated plan.

**Request body** (both endpoints):

```json
{
  "domain":          "conference",
  "category":        "AI/ML",
  "geography":       "India",
  "city":            "Bangalore",
  "target_audience": 500,
  "budget_min":      1000000,
  "budget_max":      3000000,
  "currency":        "INR",
  "event_name":      "AI Summit India 2026"
}
```

Supported domain values: `conference`, `music_festival`, `sporting_event`

```
GET /api/agents/
```

Lists all seven agents with name, description, wave number, and declared dependencies.

```
GET /api/agents/{name}/info
```

Returns metadata for a single agent by name.

### Datasets

```
GET /api/datasets/stats
```

Aggregate counts: events by domain, total sponsors, total talents, total venues.

```
GET /api/datasets/events?domain=conference&city=Bangalore&year=2024&page=1&limit=20
```

Paginated event list with optional filters.

```
GET /api/datasets/events/{id}
```

Single event with full sponsor, talent, and venue join data.

```
GET /api/datasets/search?q=blockchain+india
```

Full-text search across events, sponsors, and talents.

```
GET /api/datasets/sponsors?industry=technology
GET /api/datasets/talents?type=speaker
GET /api/datasets/venues?city=Mumbai
```

Filtered entity lists.

---

## Frontend

### Pages

| Route | Page | Description |
|---|---|---|
| `/` | LandingPage | Product overview, feature walkthrough, call to action |
| `/app` | ProjectsPage | Project list with stats, new project creation wizard |
| `/project/{id}/generating` | GeneratingPage | Live SSE agent execution with per-agent status cards |
| `/project/{id}` | ProjectDashboard | Tabbed results dashboard with navigation to all sub-pages |
| `/project/{id}/overview` | OverviewPage | Summary of all agent outputs with key metric cards |
| `/project/{id}/sponsors` | SponsorAgentPage | Sponsor recommendations table |
| `/project/{id}/speakers` | SpeakerAgentPage | Speaker recommendations table |
| `/project/{id}/venues` | VenueAgentPage | Venue comparison table |
| `/project/{id}/pricing` | PricingAgentPage | Pricing tiers and revenue projection |
| `/project/{id}/gtm` | GTMAgentPage | Community list and strategy phase timeline |
| `/project/{id}/ops` | OpsAgentPage | Event schedule and operations checklist |

### State Management

`ProjectContext` (React Context API) provides global state:

```typescript
interface ProjectContextType {
  projects:        Project[];
  addProject:      (p: Omit<Project, "id">) => Project;
  getProject:      (id: string) => Project | undefined;
  updateProject:   (id: string, updates: Partial<Project>) => void;
  agentResults:    Record<string, AgentPlan>;
  setAgentResults: (projectId: string, plan: AgentPlan) => void;
  getAgentResults: (projectId: string) => AgentPlan | undefined;
}
```

Agent results are stored in memory keyed by project ID. Pre-seeded demo projects display static mock data so the dashboard is never empty. New projects created through the wizard display results from the live API run.

### API Client

`frontend/src/lib/api.ts`:

- `buildEventConfig(project)`: Maps frontend Project fields to the backend EventConfig schema, including domain/category/geography remapping and budget defaults
- `runAgentsStream(project, onUpdate)`: Opens the SSE stream, parses events line by line, invokes the callback per update, returns the final plan on stream close
- `mapSponsors`, `mapSpeakers`, `mapVenues`, `mapPricing`, `mapGTM`, `mapOps`: Transform raw API response shapes into typed frontend display models with formatted prices, influence tiers, and rating normalization

---

## Technology Stack

### Backend

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Web framework | FastAPI 0.115+ |
| ASGI server | Uvicorn 0.30+ |
| LLM provider | Groq — Llama 3.3 70B (default), Llama 3.1 8B (fast) |
| Web search | Exa API (exa-py 1.8.8+) |
| Web scraping | crawl4ai 0.7.4+ with Playwright |
| Relational database | Supabase PostgreSQL (supabase 2.9+) |
| Vector database | Pinecone 5.0+ |
| Embeddings | BAAI/bge-m3, 1024 dimensions |
| Cache | Redis via Upstash (redis 5.0+) |
| Config | pydantic-settings 2.5+ |
| Validation | pydantic 2.9+ |

### Frontend

| Component | Technology |
|---|---|
| Language | TypeScript 5.8 |
| UI framework | React 18.3 |
| Build tool | Vite 5.4 |
| Styling | Tailwind CSS 3.4 |
| Component library | shadcn/ui (Radix UI primitives) |
| Routing | React Router 6.30 |
| Animations | Framer Motion 11 |
| Charts | Recharts 2.15 |
| Data fetching | TanStack Query 5.83 |
| Testing | Vitest 3.2 |

### Infrastructure

| Component | Platform |
|---|---|
| Backend hosting | Railway |
| Frontend hosting | Vercel |
| Container | Docker — python:3.12-slim |
| CI/CD | GitHub push to main triggers Railway auto-deploy |

---

## Local Development

### Prerequisites

- Python 3.12
- Node.js 18 or later
- A `.env` file at the repository root containing all required API keys

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive documentation (Swagger UI) is available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The development server starts at `http://localhost:5173`.

Create `frontend/.env` to configure the API base URL:

```
# Point to local backend
VITE_API_BASE_URL=http://localhost:8000

# Or point to the production Railway backend
VITE_API_BASE_URL=https://srishti-production.up.railway.app
```

### Running the Full Pipeline

With the backend running locally:

```bash
curl -X POST http://localhost:8000/api/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "conference",
    "category": "AI/ML",
    "geography": "India",
    "city": "Bangalore",
    "target_audience": 500,
    "budget_min": 1000000,
    "budget_max": 3000000,
    "currency": "INR",
    "event_name": "AI Summit India 2026"
  }'
```

Expected runtime: 37–90 seconds depending on Groq API latency and Redis cache state.

Recommended test parameters for reliable, high-quality results:

| Field | Recommended Value |
|---|---|
| Category | AI / ML or Hackathon |
| Geography | Asia Pacific |
| City | Bangalore |
| Audience Size | 300–500 |
| Budget | ₹10,00,000 – ₹30,00,000 |

---

## Deployment

### Backend (Railway)

`railway.toml` at the repository root:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"
```

`backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Pushing to the `main` branch triggers an automatic Railway redeploy. The `PORT` environment variable is injected by Railway at runtime.

### Frontend (Vercel)

1. Connect the GitHub repository to Vercel
2. Set the root directory to `frontend`
3. Add the environment variable: `VITE_API_BASE_URL=https://srishti-production.up.railway.app`
4. Deploy

Vercel runs `npm run build` and serves the output from `frontend/dist`.

---

## Environment Variables

Place these in a `.env` file at the repository root. The backend reads them via pydantic-settings.

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key for Llama 3.3 70B inference |
| `EXA_API_KEY` | Yes | Exa API key for neural web search |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase service role key |
| `DATABASE_URL` | Yes | Direct PostgreSQL connection string |
| `PINECONE_API_KEY` | Yes | Pinecone API key |
| `PINECONE_INDEX_NAME` | No | Pinecone index name (default: `srishti`) |
| `REDIS_URL` | No | Redis connection string (default: `redis://localhost:6379`) |

---

## Dataset

The platform ships with a curated seed dataset used as the Tier 1 knowledge base:

- 241 events spanning conferences, music festivals, and sporting events
- 55 cities across 11 countries, with significant India coverage including Bangalore, Mumbai, Delhi, Hyderabad, Pune, and Chennai
- Domains: AI/ML, Web3, FinTech, HealthTech, Gaming, Climate, Rock, Pop, Electronic, Cricket, Football, and Athletics
- Date range: 2019–2024, with emphasis on post-2021 events for relevance

All events were collected from public sources and normalized into the Supabase schema. Embeddings were generated using BAAI/bge-m3 and indexed in Pinecone at 1024 dimensions.

The dataset can be explored via the `/api/datasets` endpoints or directly through the Supabase dashboard. New events can be added by inserting rows into the `events` table and re-running the embedding pipeline.

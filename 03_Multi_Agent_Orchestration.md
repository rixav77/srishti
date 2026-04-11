# 03 - Multi-Agent Orchestration

---

## 1. Orchestration Framework: LangGraph

### Why LangGraph over alternatives

| Framework | Pros | Cons | Verdict |
|-----------|------|------|---------|
| **LangGraph** | Stateful graphs, cycles, checkpointing, human-in-the-loop, native LangChain | Steeper learning curve | **CHOSEN** |
| CrewAI | Simple role-based agents | Limited state management, no graph cycles | Too simple |
| AutoGen | Microsoft-backed, conversation patterns | Heavy, complex setup | Overkill |
| Custom | Full control | Build everything from scratch | Too risky for hackathon |

### LangGraph Graph Definition

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Define the shared state schema
class EventPlanState(TypedDict):
    # User input
    event_config: EventConfig
    
    # Agent outputs (populated as agents complete)
    sponsor_results: Optional[SponsorOutput]
    speaker_results: Optional[SpeakerOutput]
    exhibitor_results: Optional[ExhibitorOutput]
    venue_results: Optional[VenueOutput]
    pricing_results: Optional[PricingOutput]
    gtm_results: Optional[GTMOutput]
    ops_results: Optional[OpsOutput]
    
    # Orchestrator metadata
    current_phase: str
    completed_agents: list[str]
    errors: list[str]
    final_plan: Optional[ConsolidatedPlan]

# Build the graph
workflow = StateGraph(EventPlanState)

# Add agent nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("sponsor_agent", sponsor_agent_node)
workflow.add_node("speaker_agent", speaker_agent_node)
workflow.add_node("exhibitor_agent", exhibitor_agent_node)
workflow.add_node("venue_agent", venue_agent_node)
workflow.add_node("pricing_agent", pricing_agent_node)
workflow.add_node("gtm_agent", gtm_agent_node)
workflow.add_node("ops_agent", ops_agent_node)
workflow.add_node("synthesizer", synthesizer_node)

# Define edges (execution order)
workflow.set_entry_point("supervisor")

# Supervisor routes to Wave 1 agents (parallel)
workflow.add_conditional_edges("supervisor", route_to_agents)

# Wave 1 completes → Wave 2
workflow.add_edge("sponsor_agent", "supervisor")
workflow.add_edge("speaker_agent", "supervisor")
workflow.add_edge("venue_agent", "supervisor")

# Wave 2
workflow.add_edge("exhibitor_agent", "supervisor")

# Wave 3
workflow.add_edge("pricing_agent", "supervisor")
workflow.add_edge("gtm_agent", "supervisor")

# Wave 4
workflow.add_edge("ops_agent", "supervisor")

# Final synthesis
workflow.add_edge("synthesizer", END)

# Compile with checkpointing
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
```

---

## 2. Supervisor Agent Logic

The supervisor is the orchestrator. It decides which agents to run next based on current state.

```python
def supervisor_node(state: EventPlanState) -> dict:
    """
    Supervisor logic:
    1. Check which agents have completed
    2. Determine which agents can run next (dependencies met)
    3. Route to next wave of agents
    """
    completed = state["completed_agents"]
    
    # Wave 1: No dependencies
    wave1 = ["sponsor_agent", "speaker_agent", "venue_agent"]
    if not all(a in completed for a in wave1):
        return {"next_agents": [a for a in wave1 if a not in completed]}
    
    # Wave 2: Depends on Wave 1
    if "exhibitor_agent" not in completed:
        return {"next_agents": ["exhibitor_agent"]}
    
    # Wave 3: Depends on Wave 1 + 2
    wave3 = ["pricing_agent", "gtm_agent"]
    if not all(a in completed for a in wave3):
        return {"next_agents": [a for a in wave3 if a not in completed]}
    
    # Wave 4: Depends on all above
    if "ops_agent" not in completed:
        return {"next_agents": ["ops_agent"]}
    
    # All done → synthesize
    return {"next_agents": ["synthesizer"]}
```

---

## 3. Agent Communication via Shared State

Agents do NOT communicate peer-to-peer. All communication flows through the **shared state graph**.

### How Agents Read Each Other's Output

```python
async def pricing_agent_node(state: EventPlanState) -> dict:
    """
    Pricing Agent reads from other agents' outputs in shared state.
    """
    # Read venue costs from Venue Agent
    venue_data = state["venue_results"]
    venue_cost = venue_data["venues"][0]["pricing"]["full_event_estimate"]
    
    # Read speaker fees from Speaker Agent
    speaker_data = state["speaker_results"]
    total_speaker_cost = sum(s["estimated_fee_range_mid"] for s in speaker_data["speakers"])
    
    # Read sponsor revenue from Sponsor Agent
    sponsor_data = state["sponsor_results"]
    estimated_sponsor_revenue = calculate_sponsor_revenue(sponsor_data)
    
    # Now calculate pricing with full cost picture
    pricing_result = await calculate_optimal_pricing(
        fixed_costs=venue_cost + total_speaker_cost,
        sponsor_revenue=estimated_sponsor_revenue,
        target_audience=state["event_config"]["audience_size"],
        historical_data=await query_historical_pricing(state["event_config"])
    )
    
    return {"pricing_results": pricing_result, "completed_agents": [..., "pricing_agent"]}
```

### Shared State Schema Visualization

```
┌─────────────────────────────────────────────┐
│              EventPlanState                   │
├─────────────────────────────────────────────┤
│                                              │
│  event_config: {                             │
│    domain: "conference"                      │
│    theme: "AI & Machine Learning"            │
│    geography: "India"                        │
│    audience_size: 2000                       │
│    budget: { min: 5000000, max: 8000000 }    │
│    dates: { start: "2026-09-15", ... }       │
│  }                                           │
│                                              │
│  sponsor_results: { ... }  ← Written by      │
│  speaker_results: { ... }     respective     │
│  exhibitor_results: { ... }   agents         │
│  venue_results: { ... }                      │
│  pricing_results: { ... }  ← Reads venue +   │
│  gtm_results: { ... }        speaker data    │
│  ops_results: { ... }     ← Reads ALL above  │
│                                              │
│  final_plan: { ... }      ← Synthesizer      │
│                              merges all       │
└─────────────────────────────────────────────┘
```

---

## 4. Real-Time Streaming to Frontend

Each agent emits progress events via WebSocket as it executes.

```python
# WebSocket event types
class AgentEvent:
    AGENT_STARTED = "agent_started"
    AGENT_PROGRESS = "agent_progress"      # e.g., "Searching CrunchBase..."
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    PLAN_COMPLETED = "plan_completed"

# Example stream
# → { "type": "agent_started", "agent": "sponsor_agent", "timestamp": "..." }
# → { "type": "agent_progress", "agent": "sponsor_agent", "message": "Found 47 potential sponsors from past events", "progress": 0.3 }
# → { "type": "agent_progress", "agent": "sponsor_agent", "message": "Scoring sponsors on 5 dimensions...", "progress": 0.6 }
# → { "type": "agent_completed", "agent": "sponsor_agent", "results_summary": "25 sponsors recommended across 4 tiers", "progress": 1.0 }
```

---

## 5. Multi-Agent Collaboration Visualization

This is a **key differentiator** called out in the PDF. We will build a live, animated visualization of agent activity.

### Visualization Design

```
┌──────────────────────────────────────────────┐
│          Agent Collaboration Graph            │
│                                              │
│      [Sponsor] ──────┐                       │
│        ✅ Done       │                       │
│                      ▼                       │
│      [Speaker] ──→ [Pricing]                 │
│        ✅ Done    ⏳ Running                  │
│                      ▲                       │
│      [Venue] ───────┘                        │
│        ✅ Done                               │
│                                              │
│      [Exhibitor] ──→ [GTM]                   │
│        ✅ Done      ⏳ Queued                 │
│                                              │
│                    [Ops Agent]                │
│                    🔒 Waiting                 │
│                                              │
│  ─────────────────────────────────           │
│  Timeline: ████████████░░░░░░░  68%          │
│  Elapsed: 45s | Est. remaining: 22s          │
└──────────────────────────────────────────────┘
```

### Implementation: React Flow + WebSocket

```tsx
// Frontend: Real-time agent graph using React Flow
import ReactFlow, { Background, Controls } from 'reactflow';

const agentNodes = [
  { id: 'sponsor', data: { label: 'Sponsor Agent', status: 'completed' }, position: { x: 0, y: 0 } },
  { id: 'speaker', data: { label: 'Speaker Agent', status: 'completed' }, position: { x: 200, y: 0 } },
  { id: 'venue', data: { label: 'Venue Agent', status: 'completed' }, position: { x: 400, y: 0 } },
  { id: 'exhibitor', data: { label: 'Exhibitor Agent', status: 'completed' }, position: { x: 100, y: 150 } },
  { id: 'pricing', data: { label: 'Pricing Agent', status: 'running' }, position: { x: 200, y: 300 } },
  { id: 'gtm', data: { label: 'GTM Agent', status: 'queued' }, position: { x: 400, y: 300 } },
  { id: 'ops', data: { label: 'Ops Agent', status: 'waiting' }, position: { x: 300, y: 450 } },
];

const edges = [
  { id: 'e1', source: 'sponsor', target: 'pricing', animated: true },
  { id: 'e2', source: 'speaker', target: 'pricing', animated: true },
  { id: 'e3', source: 'venue', target: 'pricing', animated: true },
  { id: 'e4', source: 'sponsor', target: 'gtm' },
  { id: 'e5', source: 'pricing', target: 'ops' },
  { id: 'e6', source: 'gtm', target: 'ops' },
];
```

### Status Colors
- `completed` → Green with checkmark
- `running` → Blue with pulse animation
- `queued` → Yellow
- `waiting` → Gray (dependencies not met)
- `error` → Red with retry button

### Agent Activity Log (Side Panel)
Real-time log of what each agent is doing:
```
[12:45:01] Sponsor Agent → Searching CrunchBase for AI companies in India...
[12:45:03] Speaker Agent → Found 23 speakers from NeurIPS 2025 archives
[12:45:05] Venue Agent → Comparing 8 venues in Bangalore with 2000+ capacity
[12:45:08] Sponsor Agent → Scoring 47 candidates on 5 dimensions
[12:45:12] Speaker Agent → Generating outreach drafts for top 10 speakers
[12:45:15] Sponsor Agent → ✅ Complete: 25 sponsors across 4 tiers
```

---

## 6. Error Handling & Recovery

```python
# Agent-level retry with fallback
async def run_agent_with_retry(agent_fn, state, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = await agent_fn(state)
            return result
        except RateLimitError:
            await asyncio.sleep(2 ** attempt)
        except DataSourceError as e:
            # Try alternative data source
            state["fallback_mode"] = True
            continue
        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    "status": "partial",
                    "error": str(e),
                    "partial_results": get_cached_results(agent_fn.name)
                }
```

### Graceful Degradation
- If a scraper fails → fall back to cached/historical data
- If an agent times out → return partial results with confidence caveat
- If the LLM fails → retry with smaller context or simpler prompt
- Agent failures do NOT block other independent agents

---

## 7. Human-in-the-Loop (Bonus Feature)

LangGraph natively supports breakpoints where the organizer can:
1. **Review** agent recommendations before proceeding
2. **Override** a recommendation (e.g., "Remove this sponsor, add that one")
3. **Approve** and continue to next wave
4. **Adjust** parameters mid-flow (e.g., "Increase budget by 20%")

```python
# Add human checkpoint after Wave 1
workflow.add_node("human_review_wave1", human_review_node)
workflow.add_edge("supervisor", "human_review_wave1")  # After Wave 1 completes
```

This is a major differentiator -- most hackathon teams will build fully automated flows. We offer control + automation.

# 09 - Evaluation Strategy

---

## 1. Evaluation Criteria Mapping

The PDF lists 5 evaluation criteria. Here's exactly how we win each one:

### Criterion 1: Solution Quality + Real-World Applicability

**What judges look for**: Does this actually work? Could a real event organizer use this?

**Our strategy**:
- Demo with a REAL event scenario (e.g., "Plan an AI Conference in Bangalore for 2000 people")
- Show recommendations that reference REAL companies, REAL speakers, REAL venues
- Outreach drafts that are personalized (not generic templates)
- Data grounded in actual 2025-2026 events (mandatory dataset)
- Simulation dashboard that produces financially plausible numbers

**Key demo moment**: Show a sponsor recommendation and ask "would you actually reach out to this company?" -- the answer should be YES.

---

### Criterion 2: Technical Depth + Architecture Design

**What judges look for**: Is the architecture thoughtful? Is the technical implementation sophisticated?

**Our strategy**:
- **Domain-agnostic architecture** (extra points) -- show the YAML config system, switch domains live
- **LangGraph orchestration** -- proper multi-agent state management, not just sequential function calls
- **RAG pipeline** -- real vector similarity search + SQL hybrid retrieval
- **Wave-based execution** -- parallel agents where possible, sequential when dependencies exist
- **Real-time streaming** -- WebSocket updates as agents work (not just spinner → results)
- **Three-layer memory** -- conversational + episodic + semantic

**Key demo moment**: Show the architecture diagram, then show the live agent collaboration graph matching it exactly.

---

### Criterion 3: Quality of Recommendations + Intelligence

**What judges look for**: Are the AI recommendations actually smart? Context-aware or generic?

**Our strategy**:
- **Multi-dimensional scoring** -- not just "here are some sponsors," but scored on 5 specific dimensions with explanations
- **Evidence-based** -- every recommendation links back to historical data ("Sponsored 3 similar events")
- **Context-aware** -- if the event is an AI conference in India, recommend Indian AI companies, not random Fortune 500s
- **Cross-agent intelligence** -- Pricing Agent uses Venue Agent's costs; GTM Agent uses Speaker names for marketing
- **Explanations** -- natural language justification for every recommendation

**Key demo moment**: Click into a sponsor recommendation, show the 5-dimension score breakdown + evidence from past events.

---

### Criterion 4: Team Presentation + Demo

**What judges look for**: Clear communication, polished demo, confident presentation.

**Our strategy**:
- **Demo script** (see 08): rehearsed 3-5 minute flow with specific beats
- **No slides** -- live demo is the presentation. Architecture shown in the app itself
- **Fallback plan** -- pre-recorded backup video if live demo fails
- **Role clarity** -- each team member presents their area of ownership
- **"Wow" moments** -- agent graph animating, domain switch, real-time simulation

---

### Criterion 5: Novelty of Implementation + Design

**What judges look for**: Is there something creative or innovative here?

**Our unique differentiators**:

| Feature | Why It's Novel |
|---------|---------------|
| **Domain-agnostic YAML config** | Most teams will hardcode for one domain. We abstract it |
| **Live agent collaboration graph** | Visual real-time multi-agent orchestration (not just logs) |
| **Wave-based parallel execution** | Proper DAG-based agent scheduling, not sequential |
| **Three-layer AI memory** | Session + episodic + semantic memory (most teams skip memory) |
| **Simulation dashboard** | Interactive what-if scenarios (most teams stop at recommendations) |
| **Break-even + revenue projection** | Financial modeling layer (explicitly extra points per PDF) |
| **Human-in-the-loop** | Organizer can override/approve at checkpoints |
| **Personalized outreach** | AI drafts referencing actual past activities (not templates) |

---

## 2. Extra Points Strategy

The PDF explicitly mentions extra points for these items. We cover ALL of them:

| Extra Points Item | Where We Address It | Confidence |
|---|---|---|
| **Domain-agnostic architecture** | DomainConfig YAML system (01, 02, 06) | HIGH - core design decision |
| **Solution extends to multiple domains** | Conference + Music Festival + Sporting Event profiles | HIGH |
| **Event Ops/Execution Agent** | Full implementation with conflict detection (02) | HIGH |
| **Revenue projection** | Pricing Agent + Simulation Engine (05) | HIGH |
| **Ticket tier simulation** | Interactive sliders in Simulation Dashboard (05, 07) | HIGH |
| **Break-even analysis** | Break-even calculator + visualization (05, 07) | HIGH |

---

## 3. Competitive Edge vs Other Teams

Most hackathon teams will likely:
1. Build for one domain only (we do three)
2. Use sequential agent calls (we use parallel waves)
3. Skip the simulation dashboard (we make it interactive)
4. Use generic recommendations (we score on 5 dimensions with evidence)
5. Skip the data deliverable until last minute (we build it first)
6. Have no agent memory (we have three layers)
7. Show results as plain text (we have a polished dashboard + agent visualization)

---

## 4. Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| LLM API rate limiting during demo | Medium | High | Cache results, pre-computed fallback |
| Scraping sources change/block | Medium | Medium | Multiple sources per data type, cached data |
| Time overrun on agent implementation | Medium | High | Start with 4 core agents, add remaining incrementally |
| Frontend not polished enough | Medium | Medium | Use shadcn/ui for instant professional look |
| Data quality issues | Low | High | Manual spot-checking, validation pipeline |
| Pinecone free tier exceeded | Low | Medium | ChromaDB local fallback |
| Team coordination issues | Low | Medium | Clear phase ownership, daily sync |
| Demo crashes live | Low | High | Pre-recorded backup video, cached results mode |

---

## 5. Presentation Strategy

### Team Role Split (for 3-5 members)

| Role | Presentation Focus |
|------|-------------------|
| **PM/Lead** | Problem statement, solution overview, demo narration |
| **Backend Engineer 1** | Agent architecture, orchestration, LangGraph |
| **Backend Engineer 2** | Data pipeline, RAG, predictive models |
| **Frontend Engineer** | UI demo, simulation dashboard, visualization |
| **Data/ML Engineer** | Data deliverable, recommendation quality, scoring |

### Presentation Flow
1. **Problem** (30s): "Event planning is broken -- fragmented data, manual work, no intelligence"
2. **Solution** (30s): "Srishti: 7 AI agents that autonomously plan your event"
3. **Live Demo** (3 min): Full flow from wizard to results to simulation
4. **Architecture** (30s): Quick technical depth showcase
5. **Q&A ready**: Prepared answers for likely questions

### Likely Judge Questions & Prepared Answers

**Q: "How do you handle data that doesn't exist for new/unknown events?"**
A: "We use RAG to find the most similar past events and extrapolate. Our confidence scores drop for sparse data, and we flag this to the organizer."

**Q: "Why LangGraph instead of just calling APIs sequentially?"**
A: "Sequential would work but misses cross-agent context. LangGraph gives us shared state, so the Pricing Agent reads real venue costs from the Venue Agent -- not estimates."

**Q: "How accurate are the attendance predictions?"**
A: "We calibrate against historical data from similar events. For our demo dataset, the predictions are within 15-20% of actual attendance for known events."

**Q: "What happens if a scraper fails?"**
A: "Graceful degradation. We fall back to cached data, flag the gap, and continue with reduced confidence. No single failure blocks the pipeline."

**Q: "How would this work at scale?"**
A: "The architecture is stateless per request (except memory). Scaling means more Celery workers for scraping and horizontal API replicas. Pinecone and Supabase handle their own scaling."

---

## 6. Post-Submission Improvements (if time permits)

These are nice-to-haves that could differentiate further:

1. **PDF report generation** -- export the full event plan as a polished PDF
2. **Calendar integration** -- export schedule to Google Calendar/ICS
3. **Budget tracker** -- live budget vs. actual as sponsors confirm
4. **Feedback loop** -- organizer rates recommendations, system improves
5. **Multi-language support** -- outreach drafts in local language
6. **API for third parties** -- other tools can query our event intelligence

# 05 - AI & ML Features

---

## 1. Recommendation Engine

### Architecture

```
┌────────────────────────────────────────────┐
│           Recommendation Engine             │
├────────────────────────────────────────────┤
│                                            │
│  ┌──────────────┐  ┌──────────────┐        │
│  │ Retrieval    │  │ Scoring &    │        │
│  │ (Vector DB   │→ │ Ranking      │→ Output│
│  │  + SQL)      │  │ (Multi-dim)  │        │
│  └──────────────┘  └──────────────┘        │
│         ▲                   ▲              │
│         │                   │              │
│  ┌──────┴──────┐  ┌────────┴────────┐     │
│  │ Context     │  │ Domain Weights  │     │
│  │ (Event +    │  │ (from config)   │     │
│  │  History)   │  │                 │     │
│  └─────────────┘  └─────────────────┘     │
│                                            │
└────────────────────────────────────────────┘
```

### Context-Aware (NOT Generic) Recommendations

The PDF specifically says "Context-aware suggestions (not generic)." Our approach:

1. **Event context injection**: Every recommendation considers the specific event's theme, budget, geography, audience, and dates
2. **Historical grounding**: RAG retrieves similar past events and uses their outcomes to inform recommendations
3. **Cross-agent context**: Speaker recommendations consider confirmed sponsors (avoid competitor speakers), venue selection considers speaker requirements
4. **Explanation generation**: Every recommendation includes a natural language explanation of WHY it was chosen

```python
# Example: Context-aware sponsor recommendation
async def recommend_sponsors(event_config: EventConfig, memory: VectorStore) -> list:
    # Step 1: Retrieve similar past events
    similar_events = await memory.similarity_search(
        query=f"{event_config.theme} {event_config.category} conference {event_config.geography}",
        k=20,
        namespace="events"
    )
    
    # Step 2: Extract sponsors from those events
    historical_sponsors = await db.query(
        "SELECT s.*, es.tier FROM sponsors s "
        "JOIN event_sponsors es ON s.id = es.sponsor_id "
        "WHERE es.event_id = ANY($1)",
        [e.id for e in similar_events]
    )
    
    # Step 3: Expand with industry-relevant companies
    industry_sponsors = await memory.similarity_search(
        query=f"companies in {event_config.category} industry with event sponsorship history",
        k=50,
        namespace="sponsors",
        filter={"country": event_config.geography}
    )
    
    # Step 4: Score with full context
    candidates = deduplicate(historical_sponsors + industry_sponsors)
    scored = await score_sponsors(
        candidates=candidates,
        event=event_config,
        similar_events=similar_events,
        weights=domain_config.sponsor_weights
    )
    
    # Step 5: Generate explanations
    for sponsor in scored[:25]:
        sponsor.explanation = await llm.generate(
            f"Explain why {sponsor.name} is a good sponsor for {event_config.name}: "
            f"Event theme: {event_config.theme}, "
            f"Historical: {sponsor.past_sponsorships}, "
            f"Industry relevance: {sponsor.scores.industry_relevance}"
        )
    
    return scored[:25]
```

---

## 2. Search + Ranking Algorithms

### Multi-Dimensional Scoring Framework

Every entity (sponsor, speaker, venue, exhibitor, community) is scored on domain-specific dimensions. The framework is generic:

```python
class MultiDimensionalScorer:
    def __init__(self, dimensions: list[ScoringDimension]):
        self.dimensions = dimensions
    
    def score(self, candidate: dict, context: dict) -> ScoredCandidate:
        scores = {}
        for dim in self.dimensions:
            raw_score = dim.score_fn(candidate, context)        # 0.0 - 1.0
            weighted = raw_score * dim.weight
            scores[dim.name] = {"raw": raw_score, "weighted": weighted}
        
        total = sum(s["weighted"] for s in scores.values())
        return ScoredCandidate(
            candidate=candidate,
            total_score=total,
            dimension_scores=scores,
            tier=self.assign_tier(total)
        )
```

### Relevance Scoring Examples

**Sponsor Relevance Score:**
```
industry_relevance = cosine_similarity(sponsor_embedding, event_theme_embedding)
historical_score = min(1.0, past_sponsorships_count / 5)
budget_score = 1.0 if budget_in_range else gaussian_decay(distance_from_range)
frequency_score = min(1.0, sponsorships_last_year / 3)
track_record = avg_tier_score_of_past_sponsorships
```

**Speaker Relevance Score:**
```
topic_score = cosine_similarity(speaker_topics_embedding, event_topics_embedding)
history_score = log(1 + speaking_engagements_count) / log(1 + max_engagements)
influence_score = log(1 + followers) / log(1 + max_followers_in_category)
participation_score = 1.0 if spoke_at_similar_event else 0.3
```

### Hybrid Retrieval (Vector + SQL)

For best results, we combine:
1. **Vector search** (semantic similarity) — finds conceptually related entities
2. **SQL filters** (exact match) — enforces hard constraints (geography, budget, date)
3. **Re-ranking** (LLM or cross-encoder) — refines top-k results with deeper analysis

```python
async def hybrid_search(query: str, filters: dict, entity_type: str, top_k: int = 30):
    # Step 1: Vector search for semantic relevance
    vector_results = await pinecone.query(
        vector=embed(query),
        top_k=top_k * 3,  # Over-fetch
        namespace=entity_type,
        filter=filters
    )
    
    # Step 2: SQL enrichment for structured data
    ids = [r.id for r in vector_results]
    enriched = await db.query(f"SELECT * FROM {entity_type} WHERE id = ANY($1)", ids)
    
    # Step 3: Re-rank with full context
    reranked = await rerank(enriched, query, top_k=top_k)
    
    return reranked
```

---

## 3. Predictive Modeling

### 3.1 Pricing vs. Attendance Forecasting

**Model**: Gradient Boosted Trees (XGBoost/LightGBM) or simple regression

**Features:**
```
- event_category (one-hot)
- geography (one-hot)
- past_attendance_similar_events (numeric)
- speaker_quality_score (numeric, from Speaker Agent)
- ticket_price_proposed (numeric)
- days_until_event (numeric)
- marketing_budget (numeric)
- number_of_sponsors (numeric)
- community_reach (numeric, from GTM Agent)
- is_first_edition (boolean)
- competing_events_count (numeric)
- season (one-hot: Q1/Q2/Q3/Q4)
```

**Target variable**: `estimated_attendance`

**Training data**: Historical events from our mandatory dataset + any additional sources

**For hackathon**: If insufficient training data, use a **rule-based model** with LLM-calibrated estimates:

```python
async def estimate_attendance(event_config, historical_data):
    # Find 5 most similar past events
    similar = find_similar_events(event_config, historical_data, k=5)
    
    # Base estimate: median attendance of similar events
    base = median([e.attendance for e in similar])
    
    # Adjustments
    adjustments = {
        "speaker_quality": speaker_quality_multiplier(event_config.speakers),
        "pricing_effect": price_elasticity_factor(event_config.price, similar),
        "marketing_boost": marketing_multiplier(event_config.marketing_budget),
        "geography_factor": geography_adjustment(event_config.city),
    }
    
    adjusted = base * product(adjustments.values())
    
    # Confidence interval based on variance of similar events
    std = stdev([e.attendance for e in similar])
    return {
        "estimated": round(adjusted),
        "low": round(adjusted - 1.5 * std),
        "high": round(adjusted + 1.5 * std),
        "confidence": 0.7 if len(similar) >= 3 else 0.4,
        "similar_events_used": [e.name for e in similar]
    }
```

### 3.2 Conversion Rate Modeling

```
Awareness Pool (reached via marketing)
    │  × awareness_to_interest_rate (5-15%)
    ▼
Interest Pool (visited website/social)
    │  × interest_to_registration_rate (20-40%)
    ▼
Registered Pool
    │  × registration_to_payment_rate (60-80%)
    ▼
Paid Pool
    │  × payment_to_attendance_rate (80-95%)
    ▼
Actual Attendees
```

Each rate is estimated from historical data for similar events, adjusted by domain and geography.

### 3.3 Revenue Projection Model

```python
def project_revenue(pricing: PricingStrategy, demand: DemandModel, sponsors: SponsorResults):
    # Ticket revenue
    ticket_revenue = sum(
        tier.price * tier.estimated_sales
        for tier in pricing.tiers
    )
    
    # Sponsor revenue
    sponsor_revenue = sum(
        estimate_sponsor_package_value(s.recommended_tier)
        for s in sponsors.confirmed_sponsors
    )
    
    # Exhibitor revenue
    exhibitor_revenue = exhibitor_count * avg_booth_fee
    
    # Total
    total = ticket_revenue + sponsor_revenue + exhibitor_revenue
    
    # Costs
    fixed_costs = venue_cost + speaker_fees + marketing + operations
    variable_costs = per_attendee_cost * demand.estimated_attendance
    
    return {
        "total_revenue": total,
        "total_costs": fixed_costs + variable_costs,
        "profit": total - (fixed_costs + variable_costs),
        "margin": (total - fixed_costs - variable_costs) / total,
        "breakdown": {
            "tickets": ticket_revenue,
            "sponsors": sponsor_revenue,
            "exhibitors": exhibitor_revenue
        }
    }
```

---

## 4. Simulation Dashboard (What-If Scenarios)

### Extra Points Feature: This is explicitly called out as "particularly valued"

### What-If Scenarios Supported

| Scenario | Input Controls | Output Changes |
|----------|---------------|----------------|
| **Price adjustment** | Slider: ±50% per tier | Attendance change, revenue change, margin |
| **Tier restructure** | Add/remove tiers, change allocation | Revenue redistribution, conversion changes |
| **Venue change** | Select different venue | Cost change, capacity impact, location score |
| **Marketing budget** | Slider: ±100% | Reach change, registration change, ROI |
| **Speaker lineup change** | Add/remove speakers | Quality score, attendance impact, cost |
| **Date change** | Calendar picker | Competing events, seasonal demand |

### Break-Even Analysis (Extra Points)

```
Revenue Line: y = (avg_ticket_price × x) + sponsor_revenue + exhibitor_revenue
Cost Line:    y = fixed_costs + (variable_cost_per_attendee × x)

Break-even point: where Revenue = Cost
    x = (fixed_costs - sponsor_revenue - exhibitor_revenue) / (avg_ticket_price - variable_cost_per_attendee)
```

**Visualization**: Interactive chart showing:
- Revenue curve (increasing with attendance)
- Cost curve (fixed + variable)
- Break-even point highlighted
- Current projected attendance marked
- Safety margin shown

### Ticket Tier Simulation (Extra Points)

Interactive UI where the organizer can:
1. Drag sliders to adjust tier prices
2. See real-time changes in projected attendance per tier
3. See total revenue update instantly
4. Compare multiple pricing scenarios side-by-side

```tsx
// Simulation controls (React component concept)
<SimulationPanel>
  <TierSlider tier="Early Bird" price={4999} allocation={20} />
  <TierSlider tier="Regular" price={7999} allocation={40} />
  <TierSlider tier="VIP" price={19999} allocation={10} />
  <TierSlider tier="Student" price={2999} allocation={30} />
  
  <RevenueProjection total={8500000} />
  <BreakEvenChart breakEvenAt={850} projected={2000} />
  <AttendanceForcast byTier={...} total={2000} />
</SimulationPanel>
```

---

## 5. Autonomous Outreach Drafts

### PDF Requirement: "Autonomous outreach drafts (not generic)"

Each outreach draft is **personalized** using:
1. The recipient's profile data (company, role, past activities)
2. The event's specific details (theme, dates, audience)
3. The relevance score and evidence (why this person/company is a fit)

### Outreach Types

| Type | Target | Channel | Agent |
|------|--------|---------|-------|
| Sponsor pitch | Company decision-makers | Email + LinkedIn | Sponsor Agent |
| Speaker invite | Potential speakers | Email + LinkedIn | Speaker Agent |
| Exhibitor pitch | Companies with booth potential | Email | Exhibitor Agent |
| Community partnership | Community organizers | Email + DM | GTM Agent |

### Draft Generation Prompt Template

```python
SPONSOR_OUTREACH_PROMPT = """
You are drafting a sponsorship outreach email for {event_name}.

Recipient: {company_name} ({industry})
Their past sponsorships: {past_sponsorships}
Why they're a fit: {relevance_explanation}
Recommended tier: {tier} (${tier_price})

Event details:
- Theme: {theme}
- Date: {dates}
- Location: {location}
- Expected attendance: {attendance}
- Notable speakers: {speakers}

Generate:
1. Email subject line (compelling, not spammy)
2. Email body (professional, personalized, 150-200 words)
3. LinkedIn connection message (60 words max)

The tone should be professional but warm. Reference their specific past activities.
Do NOT be generic. Do NOT use cliches like "exciting opportunity."
"""
```

### Output Example
```json
{
  "email": {
    "subject": "Google Cloud x AI Summit India 2026 - Title Sponsorship",
    "body": "Hi [Name],\n\nI noticed Google Cloud's strong presence at GTC India 2025 and DevFest Bangalore — your commitment to the Indian AI ecosystem is impressive.\n\nWe're organizing AI Summit India 2026 (Sep 15-17, Bangalore, 2000+ attendees) and believe Google Cloud would be an exceptional Title Sponsor. Our audience — ML engineers, AI researchers, and CTOs — aligns perfectly with your cloud AI platform push.\n\nThe Title Sponsor package includes...\n\nWould you be open to a 15-minute call next week to explore this?\n\nBest,\n[Organizer]"
  },
  "linkedin": {
    "message": "Hi [Name], loved Google Cloud's booth at DevFest Bangalore. We're planning AI Summit India 2026 (2000+ AI engineers) and think Google Cloud would be a perfect Title Sponsor. Would love to share details — open to connecting?"
  }
}
```

---

## 6. AI Agent Memory Architecture

### Three Memory Layers

```
┌─────────────────────────────────────────┐
│ Layer 1: Conversational Memory          │
│ (LangGraph Checkpoints)                 │
│ - Current session state                 │
│ - Agent conversation history            │
│ - User preferences within session       │
│ TTL: Session duration                   │
├─────────────────────────────────────────┤
│ Layer 2: Episodic Memory                │
│ (Pinecone - session namespace)          │
│ - Past event planning sessions          │
│ - User feedback on recommendations      │
│ - Successful/failed suggestions         │
│ TTL: Persistent                         │
├─────────────────────────────────────────┤
│ Layer 3: Semantic Memory                │
│ (Pinecone - knowledge namespace)        │
│ - Event knowledge base (mandatory data) │
│ - Sponsor/speaker/venue databases       │
│ - Industry knowledge embeddings         │
│ TTL: Updated by scraping pipelines      │
└─────────────────────────────────────────┘
```

### Memory Retrieval Priority
1. First check **conversational memory** (most recent, most relevant to current session)
2. Then query **episodic memory** (past sessions, user preferences)
3. Finally search **semantic memory** (general knowledge base)

This ensures agents "remember" past interactions and get better over time.

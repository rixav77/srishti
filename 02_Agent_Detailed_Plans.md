# 02 - Agent Detailed Plans

> Every agent follows a standard interface: receives domain config + event context, queries data layer, scores/ranks results, and returns structured output to shared state.

---

## Agent Standard Interface

```python
class BaseAgent:
    """Every agent implements this interface."""
    
    def __init__(self, domain_config: DomainConfig, memory: VectorStore, db: Database):
        self.domain = domain_config
        self.memory = memory    # Pinecone/ChromaDB for RAG
        self.db = db            # PostgreSQL for structured queries
    
    async def execute(self, state: SharedState) -> AgentOutput:
        """Main execution method called by orchestrator."""
        pass
    
    async def score_and_rank(self, candidates: list) -> list:
        """Score candidates using domain-specific weights."""
        pass
    
    async def generate_explanation(self, results: list) -> str:
        """LLM-generated explanation of why these results were chosen."""
        pass
```

**Output format** (every agent):
```json
{
  "agent_name": "sponsor_agent",
  "status": "completed",
  "results": [ ... ],
  "confidence_score": 0.87,
  "explanation": "Based on historical data from 47 similar events...",
  "data_sources_used": ["crunchbase", "linkedin", "past_events_db"],
  "recommendations_count": 15,
  "execution_time_ms": 4200
}
```

---

## Agent 1: Sponsor Agent

### Purpose
Recommend potential sponsors for the event, categorized by tier, scored by relevance.

### Inputs (from shared state)
- Event category/theme (e.g., "AI Conference")
- Geography (e.g., "India")
- Target audience size (e.g., 2000)
- Estimated budget range
- Event date(s)

### Process Flow
```
1. Query historical data: "Which companies sponsored similar events in 2024-2026?"
2. Scrape/query CrunchBase + LinkedIn for companies in the event's industry
3. Filter by geography and budget relevance
4. Score each potential sponsor on 5 dimensions
5. Categorize into tiers (Title / Gold / Silver / Bronze)
6. Generate outreach drafts for top sponsors
7. Return ranked list with explanations
```

### Scoring Dimensions (weighted)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Industry Relevance** | 0.30 | How closely the company's industry matches the event theme |
| **Historical Sponsorship** | 0.25 | Has the company sponsored similar events before? How many? |
| **Budget Relevance** | 0.20 | Does the company's marketing spend align with sponsorship tiers? |
| **Sponsoring Frequency** | 0.15 | How actively does the company sponsor events (last 12 months)? |
| **Track Record** | 0.10 | Quality of past sponsorships (tier level, engagement, renewals) |

### Tier Assignment Logic
```
Total Score >= 0.85 → Title Sponsor candidate
Total Score >= 0.70 → Gold Sponsor candidate  
Total Score >= 0.50 → Silver Sponsor candidate
Total Score >= 0.30 → Bronze Sponsor candidate
Below 0.30 → Not recommended
```

### Tools Available to This Agent
- `search_past_sponsors(category, geography, year_range)` — queries PostgreSQL
- `search_crunchbase(industry, geography, funding_stage)` — API/scraper
- `search_linkedin_companies(keywords, geography, size)` — scraper
- `vector_search_sponsors(query_embedding, top_k)` — Pinecone RAG
- `generate_outreach_email(sponsor, event, tier)` — LLM-generated draft
- `calculate_sponsor_score(sponsor, event_context)` — scoring function

### Output Schema
```json
{
  "sponsors": [
    {
      "rank": 1,
      "company_name": "Google Cloud",
      "recommended_tier": "Title",
      "total_score": 0.92,
      "scores": {
        "industry_relevance": 0.95,
        "historical_sponsorship": 0.90,
        "budget_relevance": 0.88,
        "sponsoring_frequency": 0.93,
        "track_record": 0.91
      },
      "evidence": {
        "past_sponsorships": ["Google I/O 2025", "DevFest India 2025"],
        "estimated_marketing_budget": "High",
        "industry_match": "Cloud computing directly relevant to AI conference"
      },
      "outreach_draft": {
        "email_subject": "Partnership Opportunity: [Event Name] 2026",
        "email_body": "...",
        "linkedin_message": "..."
      },
      "data_sources": ["crunchbase", "past_events_db", "linkedin"]
    }
  ],
  "tier_summary": {
    "title": 3,
    "gold": 5,
    "silver": 7,
    "bronze": 10
  }
}
```

### Domain Adaptations
- **Conferences**: Standard corporate sponsors (tech companies, SaaS, cloud providers)
- **Music Festivals**: Beverage brands, lifestyle brands, streaming platforms, audio companies
- **Sporting Events**: Sportswear brands, beverage companies, betting platforms, broadcast networks

---

## Agent 2: Speaker/Artist Agent

### Purpose
Identify and recommend speakers (conferences), artists (music festivals), or athletes/commentators (sporting events) via LinkedIn, web sources, and historical data.

### Inputs
- Event category/theme
- Specific topics/genres needed
- Geography
- Budget for speaker fees
- Event prestige level (estimated from audience size + past data)

### Process Flow
```
1. Query past events: "Who spoke at similar events in the last 2 years?"
2. Search LinkedIn for domain experts matching topics
3. Search Sessionize/PaperCall/conference archives for active speakers
4. Score candidates on 4 dimensions
5. Generate outreach drafts for top candidates
6. Return ranked list grouped by session type (keynote, panel, workshop)
```

### Scoring Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Topic Relevance** | 0.35 | Expertise alignment with event themes/tracks |
| **Speaking History** | 0.25 | Number and quality of past speaking engagements |
| **Influence** | 0.25 | Follower count, publications, H-index, streams (domain-dependent) |
| **Past Event Participation** | 0.15 | Did they participate in similar events before? |

### Tools
- `search_past_speakers(category, topics, year_range)` — PostgreSQL
- `search_linkedin_people(keywords, title, geography)` — scraper
- `search_sessionize(topics)` — API
- `search_spotify_artists(genre, popularity_min)` — API (music domain)
- `vector_search_speakers(query_embedding, top_k)` — Pinecone RAG
- `generate_speaker_outreach(speaker, event)` — LLM draft

### Output Schema
```json
{
  "speakers": [
    {
      "rank": 1,
      "name": "Dr. Andrej Karpathy",
      "role": "Keynote Speaker",
      "topic_match": ["LLMs", "AI Safety", "Neural Networks"],
      "total_score": 0.94,
      "scores": {
        "topic_relevance": 0.98,
        "speaking_history": 0.95,
        "influence": 0.92,
        "past_participation": 0.85
      },
      "profile": {
        "current_role": "Independent AI Researcher",
        "linkedin_url": "...",
        "followers": 850000,
        "notable_talks": ["Tesla AI Day", "NeurIPS 2024"],
        "publications": 45
      },
      "outreach_draft": { "email_subject": "...", "email_body": "...", "linkedin_message": "..." },
      "estimated_fee_range": "$20,000 - $50,000"
    }
  ],
  "session_distribution": {
    "keynotes": 3,
    "panels": 8,
    "workshops": 5,
    "lightning_talks": 12
  }
}
```

### Domain Adaptations
- **Conferences**: LinkedIn profiles, Google Scholar, Sessionize, PaperCall
- **Music Festivals**: Spotify API (monthly listeners, genres), Bandsintown, Songkick
- **Sporting Events**: ESPN profiles, sports databases, athlete social media followings

---

## Agent 3: Exhibitor Agent

### Purpose
Identify companies/organizations that exhibited at similar events. Suggest potential exhibitors. Cluster by category.

### Inputs
- Event category/theme
- Geography
- Expected attendee profile (roles, industries)
- Exhibition space budget/capacity

### Process Flow
```
1. Query past events for exhibitor lists
2. Search for companies in relevant industries
3. Identify companies with active event marketing presence
4. Cluster into categories (startup, enterprise, tools, individual)
5. Score by relevance and likelihood to exhibit
6. Return categorized, ranked exhibitor list
```

### Scoring Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Industry Fit** | 0.30 | Product/service alignment with event attendees |
| **Exhibition History** | 0.25 | Past exhibition at similar events |
| **Company Stage** | 0.20 | Startup vs enterprise (affects booth type/spend) |
| **Marketing Activity** | 0.15 | Active event marketing budget signals |
| **Geographic Presence** | 0.10 | Presence in the event's geography |

### Categories
- **Startup**: < 50 employees, < Series B
- **Enterprise**: > 500 employees, established brands
- **Tools/Platform**: SaaS, developer tools, B2B platforms
- **Individual/Boutique**: Solo creators, small agencies, artisans
- **Non-Profit/Community**: Open-source, foundations, academic

### Output Schema
```json
{
  "exhibitors": [
    {
      "rank": 1,
      "company_name": "Hugging Face",
      "category": "Tools/Platform",
      "total_score": 0.89,
      "exhibition_history": ["NeurIPS 2025", "ICML 2025"],
      "relevance_explanation": "Open-source ML platform, directly relevant to AI conference attendees",
      "estimated_booth_tier": "Premium",
      "contact_info": { "type": "inferred", "channel": "partnerships@huggingface.co" }
    }
  ],
  "category_distribution": {
    "startup": 15,
    "enterprise": 8,
    "tools_platform": 12,
    "individual": 5,
    "non_profit": 3
  }
}
```

---

## Agent 4: Venue Agent

### Purpose
Recommend venues based on estimated crowd size, geography, budget. Include capacity, pricing, past event usage, location data.

### Inputs
- Geography (city/region/country)
- Expected attendance (from user input + Pricing Agent estimates)
- Budget range for venue
- Event type requirements (indoor/outdoor/hybrid)
- Date range
- Special requirements (AV, breakout rooms, stage setup, catering)

### Process Flow
```
1. Query venue database for geography + capacity match
2. Search Google Maps/venue directories for options
3. Cross-reference with past event usage (which venues hosted similar events)
4. Score venues on 6 dimensions
5. Generate comparison table
6. Return ranked list with maps/logistics data
```

### Scoring Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Capacity Fit** | 0.25 | How well capacity matches expected attendance (±20% ideal) |
| **Budget Fit** | 0.20 | Venue cost within budget range |
| **Location Quality** | 0.20 | Accessibility, transport links, nearby hotels |
| **Past Event Track Record** | 0.15 | Successfully hosted similar events before |
| **Amenities** | 0.10 | AV equipment, breakout rooms, catering, parking |
| **Availability** | 0.10 | Available for requested dates |

### Output Schema
```json
{
  "venues": [
    {
      "rank": 1,
      "name": "Bangalore International Exhibition Centre",
      "city": "Bangalore",
      "country": "India",
      "total_score": 0.91,
      "capacity": { "max": 5000, "recommended": 3000, "breakout_rooms": 12 },
      "pricing": { "daily_rate": "$15,000", "full_event_estimate": "$45,000" },
      "past_events": ["TechSummit India 2025", "AI Conference Bangalore 2024"],
      "location_data": {
        "address": "...",
        "coordinates": { "lat": 12.97, "lng": 77.59 },
        "nearest_airport": "BLR (8km)",
        "nearby_hotels": 15,
        "public_transport": "Metro Purple Line - 500m"
      },
      "amenities": ["Built-in AV", "Catering kitchen", "WiFi 1Gbps", "Parking 500 cars"],
      "type": "indoor",
      "images": ["url1", "url2"]
    }
  ]
}
```

### Domain Adaptations
- **Conferences**: Convention centers, hotels, university campuses
- **Music Festivals**: Parks, fairgrounds, arenas, amphitheaters (outdoor focus)
- **Sporting Events**: Stadiums, arenas, sports complexes

---

## Agent 5: Pricing & Footfall Agent

### Purpose
Determine optimal ticket pricing with tiers, model pricing vs. attendance relationship, estimate conversion rates and demand.

### Inputs
- Event category/theme
- Geography + target audience size
- Venue costs (from Venue Agent)
- Speaker costs (from Speaker Agent)
- Sponsor revenue estimates (from Sponsor Agent)
- Historical pricing data from similar events

### Process Flow
```
1. Gather historical pricing data for similar events
2. Analyze pricing vs. attendance correlations
3. Model demand curves for different price points
4. Calculate optimal pricing for each tier
5. Estimate conversion rates (registrations → attendees)
6. Generate revenue projections
7. Run break-even analysis
8. Output pricing strategy with confidence intervals
```

### Pricing Tier Structure (domain-adaptive)

**Conferences:**
| Tier | Typical Range | Conversion Rate |
|------|--------------|-----------------|
| Super Early Bird | 40-50% of Regular | 15-20% |
| Early Bird | 60-70% of Regular | 25-30% |
| Regular | Base price | 35-40% |
| VIP | 200-300% of Regular | 5-10% |
| Student | 30-40% of Regular | 10-15% |

**Music Festivals:**
| Tier | Typical Range | Conversion Rate |
|------|--------------|-----------------|
| Early Bird GA | 60-70% of Regular GA | 20-25% |
| General Admission | Base price | 40-50% |
| VIP | 200-400% of GA | 10-15% |
| Backstage/Premium | 500%+ of GA | 2-5% |

### Models Used
1. **Price Elasticity Model**: How attendance changes with price changes
2. **Demand Forecasting**: Time-series + features (event reputation, speaker quality, marketing spend)
3. **Conversion Funnel**: Awareness → Interest → Registration → Payment → Attendance
4. **Break-Even Calculator**: Fixed costs + variable costs vs. revenue streams

### Output Schema
```json
{
  "pricing_strategy": {
    "tiers": [
      {
        "name": "Early Bird",
        "price": 4999,
        "currency": "INR",
        "allocation_pct": 20,
        "estimated_sales": 400,
        "revenue": 1999600
      }
    ],
    "total_projected_revenue": 8500000,
    "break_even_attendees": 850,
    "confidence_interval": { "low": 7200000, "high": 9800000 }
  },
  "demand_model": {
    "estimated_total_attendees": 2000,
    "attendance_by_tier": { ... },
    "conversion_rates": {
      "awareness_to_interest": 0.15,
      "interest_to_registration": 0.35,
      "registration_to_payment": 0.70,
      "payment_to_attendance": 0.85
    }
  },
  "sensitivity_analysis": {
    "price_increase_10pct": { "attendance_change": "-8%", "revenue_change": "+1.5%" },
    "price_decrease_10pct": { "attendance_change": "+12%", "revenue_change": "-0.5%" }
  },
  "break_even": {
    "fixed_costs": 3500000,
    "variable_cost_per_attendee": 500,
    "break_even_point": 850,
    "margin_of_safety": "57.5%"
  }
}
```

---

## Agent 6: Community & GTM Agent

### Purpose
Identify relevant communities/forums for promotion, suggest partnership strategies, and generate Go-to-Market messaging.

### Inputs
- Event category/theme
- Target audience profile (roles, industries, seniority)
- Geography
- Budget for marketing
- Timeline to event

### Process Flow
```
1. Search for relevant communities (LinkedIn groups, Reddit, Discord, Slack, Meetup)
2. Score communities by size, activity, and audience match
3. Identify potential community partners (co-promoters, media partners)
4. Generate GTM strategy (channels, messaging, timeline)
5. Draft promotional content for each channel
6. Suggest community partnership outreach
```

### Community Scoring

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Audience Match** | 0.35 | Member demographics match target attendees |
| **Community Size** | 0.20 | Number of active members |
| **Activity Level** | 0.20 | Posts per week, engagement rate |
| **Geographic Relevance** | 0.15 | Members in target geography |
| **Partnership History** | 0.10 | Has partnered with events before |

### Output Schema
```json
{
  "communities": [
    {
      "rank": 1,
      "name": "MLOps Community",
      "platform": "Slack",
      "members": 15000,
      "activity": "High (200+ posts/week)",
      "audience_match": 0.92,
      "total_score": 0.88,
      "partnership_suggestion": "Offer 20% discount code for members + community spotlight session",
      "contact": "community-lead@mlops.community"
    }
  ],
  "gtm_strategy": {
    "phases": [
      {
        "name": "Awareness (T-12 weeks)",
        "channels": ["LinkedIn", "Twitter/X", "Reddit"],
        "actions": ["Announce event", "Early bird launch", "Speaker reveals"],
        "content_drafts": { "linkedin_post": "...", "tweet_thread": "...", "reddit_post": "..." }
      },
      {
        "name": "Consideration (T-8 weeks)",
        "channels": ["Email", "Community partnerships", "Retargeting"],
        "actions": ["Partner promotions", "Agenda reveal", "Testimonials"]
      },
      {
        "name": "Conversion (T-4 weeks)",
        "channels": ["Email", "Social", "Direct outreach"],
        "actions": ["Last call pricing", "FOMO content", "Group discount push"]
      }
    ],
    "estimated_reach": 250000,
    "estimated_registrations_from_gtm": 800
  },
  "messaging": {
    "tagline": "Where AI builders shape the future",
    "value_props": ["Learn from industry leaders", "Network with 2000+ peers", "Hands-on workshops"],
    "tone": "Professional but energetic"
  }
}
```

### Domain Adaptations
- **Conferences**: LinkedIn, Twitter/X, Reddit, Slack/Discord dev communities
- **Music Festivals**: Instagram, TikTok, Spotify playlists, music blogs, fan forums
- **Sporting Events**: Sports subreddits, fan clubs, fantasy sports platforms, team social media

---

## Agent 7: Event Ops/Execution Agent (HIGHLY RECOMMENDED - Extra Points)

### Purpose
Build the event agenda/schedule, detect conflicts, plan resource allocation (rooms, speakers, timing).

### Inputs (depends on ALL other agents)
- Speaker/artist list (from Speaker Agent)
- Venue details (from Venue Agent) — rooms, stages, capacity
- Event duration and dates
- Track/theme structure
- Sponsor commitments (from Sponsor Agent) — sponsored sessions, booths
- Exhibitor list (from Exhibitor Agent) — booth assignments

### Process Flow
```
1. Collect all resource constraints (rooms, times, speakers, tracks)
2. Generate initial schedule using constraint satisfaction
3. Detect and resolve conflicts:
   - Speaker double-booked
   - Room over-capacity
   - Topic clustering (don't schedule competing sessions)
4. Optimize for attendee experience:
   - Balance popular and niche sessions
   - Proper breaks and networking time
   - Logical topic flow within tracks
5. Assign resources (rooms, AV, catering per session)
6. Output visual schedule + resource plan
```

### Conflict Detection Rules
1. **Speaker conflict**: Same speaker in overlapping time slots
2. **Room conflict**: Room booked for multiple sessions at same time
3. **Capacity conflict**: Session expected attendees > room capacity
4. **Topic conflict**: Multiple high-demand sessions on same topic at same time
5. **Sponsor conflict**: Competing sponsor sessions scheduled adjacently
6. **Break conflict**: No breaks between sessions in same room

### Output Schema
```json
{
  "schedule": {
    "days": [
      {
        "date": "2026-09-15",
        "slots": [
          {
            "time": "09:00-10:00",
            "type": "keynote",
            "title": "Opening Keynote: The Future of AI",
            "speaker": "Dr. Andrej Karpathy",
            "room": "Main Hall",
            "capacity": 2000,
            "track": "General"
          }
        ]
      }
    ]
  },
  "conflicts_detected": 0,
  "conflicts_resolved": 3,
  "resource_plan": {
    "rooms_used": 8,
    "total_sessions": 45,
    "av_requirements": { ... },
    "catering_schedule": { ... }
  },
  "optimization_notes": [
    "Moved 'MLOps Workshop' from Room B to Room D (capacity 50→150) due to high interest signals"
  ]
}
```

---

## Cross-Agent Dependencies

```
                    ┌──────────┐
                    │  User    │
                    │  Input   │
                    └────┬─────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
    ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
    │  Sponsor   │ │  Speaker  │ │  Venue    │
    │  Agent     │ │  Agent    │ │  Agent    │
    └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
          │              │              │
          │         ┌────▼────┐         │
          │         │Exhibitor│         │
          │         │ Agent   │         │
          │         └────┬────┘         │
          │              │              │
          └──────┬───────┴───────┬──────┘
                 │               │
          ┌──────▼──────┐ ┌─────▼──────┐
          │ Pricing &   │ │ Community  │
          │ Footfall    │ │ & GTM      │
          └──────┬──────┘ └─────┬──────┘
                 │               │
                 └───────┬───────┘
                         │
                  ┌──────▼──────┐
                  │ Event Ops   │
                  │ Agent       │
                  └─────────────┘
```

**Execution order:**
1. **Parallel (Wave 1)**: Sponsor Agent, Speaker Agent, Venue Agent (independent)
2. **Wave 2**: Exhibitor Agent (can benefit from sponsor data)
3. **Wave 3**: Pricing Agent (needs venue costs + speaker fees), Community/GTM Agent (needs speaker names for marketing)
4. **Wave 4**: Event Ops Agent (needs all above to build schedule)

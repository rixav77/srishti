# 04 - Data Strategy

---

## 1. The Data Fragmentation Problem

The #1 core challenge: event data is scattered across LinkedIn, event sites, CRMs, and unstructured sources. Our Data Aggregation Layer solves this with a **unified schema + multi-source ingestion pipeline**.

---

## 2. Unified Data Schema

All data from all sources normalizes into these core tables:

### Events Table
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT NOT NULL,           -- 'conference' | 'music_festival' | 'sporting_event'
    category TEXT,                  -- 'AI', 'Web3', 'Rock', 'Cricket', etc.
    subcategory TEXT,
    description TEXT,
    start_date DATE,
    end_date DATE,
    city TEXT,
    country TEXT,
    continent TEXT,
    venue_name TEXT,
    estimated_attendance INTEGER,
    actual_attendance INTEGER,
    ticket_price_min NUMERIC,
    ticket_price_max NUMERIC,
    currency TEXT DEFAULT 'USD',
    website_url TEXT,
    year INTEGER,
    data_source TEXT,               -- 'scraped_eventbrite' | 'manual' | 'api_conftech'
    extraction_method TEXT,         -- 'playwright_scraper' | 'api' | 'manual_entry'
    scraped_at TIMESTAMP,
    raw_data JSONB,                 -- Original unprocessed data
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Sponsors Table
```sql
CREATE TABLE sponsors (
    id UUID PRIMARY KEY,
    company_name TEXT NOT NULL,
    industry TEXT,
    company_size TEXT,              -- 'startup' | 'mid' | 'enterprise'
    headquarters_country TEXT,
    linkedin_url TEXT,
    website_url TEXT,
    estimated_revenue TEXT,
    data_source TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE event_sponsors (
    event_id UUID REFERENCES events(id),
    sponsor_id UUID REFERENCES sponsors(id),
    tier TEXT,                       -- 'title' | 'gold' | 'silver' | 'bronze'
    estimated_amount NUMERIC,
    PRIMARY KEY (event_id, sponsor_id)
);
```

### Speakers/Artists Table
```sql
CREATE TABLE talents (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,                       -- 'speaker' | 'artist' | 'athlete'
    title TEXT,
    organization TEXT,
    linkedin_url TEXT,
    twitter_url TEXT,
    spotify_url TEXT,                -- music domain
    topics TEXT[],                   -- ['AI', 'MLOps', 'LLMs']
    follower_count INTEGER,
    publications_count INTEGER,
    monthly_listeners INTEGER,       -- music domain
    data_source TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE event_talents (
    event_id UUID REFERENCES events(id),
    talent_id UUID REFERENCES talents(id),
    role TEXT,                       -- 'keynote' | 'panel' | 'workshop' | 'headliner'
    session_title TEXT,
    PRIMARY KEY (event_id, talent_id)
);
```

### Venues Table
```sql
CREATE TABLE venues (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    country TEXT,
    type TEXT,                       -- 'convention_center' | 'hotel' | 'stadium' | 'outdoor'
    max_capacity INTEGER,
    address TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    website_url TEXT,
    amenities TEXT[],
    daily_rate_estimate NUMERIC,
    currency TEXT DEFAULT 'USD',
    past_event_count INTEGER,
    data_source TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Communities Table
```sql
CREATE TABLE communities (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    platform TEXT,                   -- 'linkedin' | 'reddit' | 'discord' | 'slack' | 'meetup'
    url TEXT,
    member_count INTEGER,
    activity_level TEXT,             -- 'high' | 'medium' | 'low'
    topics TEXT[],
    geography TEXT,
    data_source TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 3. Data Sources & Ingestion Pipelines

### 3.1 Source Priority (by reliability)

| Priority | Source Type | Examples | Reliability |
|----------|-----------|----------|-------------|
| 1 | **Structured APIs** | Eventbrite API, Meetup API, Spotify API | High |
| 2 | **Semi-structured websites** | conf.tech, Luma, sessionize.com | Medium-High |
| 3 | **Web scraping** | Event websites, LinkedIn, CrunchBase | Medium |
| 4 | **Manual curation** | Team research, Wikipedia event lists | High but slow |
| 5 | **LLM-assisted extraction** | Unstructured web pages parsed by LLM | Medium |

### 3.2 Scraping Pipelines (by domain)

#### Conference Data Sources

| Source | What We Get | Method |
|--------|------------|--------|
| **conf.tech** | Tech conference list, dates, locations | API / light scrape |
| **Eventbrite** | Events, ticket prices, attendance | API (free tier) |
| **Luma** | Tech events, speakers, RSVPs | Scrape |
| **Sessionize** | Speaker profiles, talk history | API |
| **PaperCall** | CFP data, speaker submissions | Scrape |
| **LinkedIn** | Company data, people profiles | Scrape (careful with rate limits) |
| **CrunchBase** | Company funding, industry, size | API (free tier) |
| **Google Maps** | Venue data, capacity, reviews | Places API |
| **dev.events** | Developer conference aggregator | Scrape |
| **10times.com** | Global event directory | Scrape |

#### Music Festival Data Sources

| Source | What We Get | Method |
|--------|------------|--------|
| **Songkick** | Festival lineups, dates, locations | API |
| **Bandsintown** | Artist tour data, venues | API |
| **Festicket** | Festival details, ticket prices | Scrape |
| **Spotify** | Artist popularity, genres, listeners | API |
| **Pollstar** | Concert industry data | Scrape |
| **JamBase** | Festival directory | Scrape |

#### Sporting Event Data Sources

| Source | What We Get | Method |
|--------|------------|--------|
| **ESPN** | Events, athletes, venues | Scrape/API |
| **StubHub** | Ticket prices, demand signals | Scrape |
| **Google Sports** | Event schedules, results | Scrape |
| **Transfermarkt** | Athlete/team data | Scrape |

### 3.3 Scraper Architecture

```python
# Scraper base class
class BaseScraper:
    def __init__(self, source_name: str, rate_limit: float = 1.0):
        self.source = source_name
        self.rate_limit = rate_limit  # requests per second
        self.browser = None           # Playwright browser (lazy init)
    
    async def scrape(self, params: dict) -> list[dict]:
        """Override in subclass."""
        raise NotImplementedError
    
    async def normalize(self, raw_data: list[dict]) -> list[dict]:
        """Convert source-specific format to unified schema."""
        raise NotImplementedError
    
    async def store(self, normalized_data: list[dict]):
        """Insert into PostgreSQL + generate embeddings for Pinecone."""
        await self.db.bulk_insert(normalized_data)
        embeddings = await self.embed(normalized_data)
        await self.vector_db.upsert(embeddings)
```

**Tech stack for scraping:**
- **Playwright** (Python) for JavaScript-heavy sites
- **httpx + BeautifulSoup** for simple HTML pages
- **Celery + Redis** for background job scheduling
- **Rotating proxies** if needed (but minimize aggressive scraping)

### 3.4 ETL Pipeline Flow

```
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐
│  Source   │ →  │  Extract  │ →  │ Transform │ →  │  Load    │ →  │  Embed   │
│  (Web/   │    │  (Scraper │    │ (Normalize│    │(Postgres)│    │(Pinecone)│
│   API)   │    │   /API)   │    │  +Clean)  │    │          │    │          │
└──────────┘    └───────────┘    └───────────┘    └──────────┘    └──────────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │ Deduplication │
                                │ + Validation  │
                                └──────────────┘
```

**Transform steps:**
1. Parse raw HTML/JSON into structured fields
2. Normalize dates to ISO 8601
3. Normalize locations to `city, country` format
4. Normalize currency to USD (with original preserved)
5. Deduplicate by (event_name + year + city) composite key
6. Validate: reject records missing name + date
7. Tag with `data_source` and `extraction_method`

---

## 4. RAG / Vector Database Strategy

### 4.1 What Gets Embedded

| Entity Type | Embedding Content | Use Case |
|------------|-------------------|----------|
| Events | `{name} {category} {description} {city} {year}` | "Find events similar to NeurIPS" |
| Sponsors | `{company_name} {industry} {description}` | "Find sponsors in cloud computing" |
| Speakers | `{name} {title} {topics joined} {bio}` | "Find speakers on MLOps" |
| Venues | `{name} {city} {type} {amenities joined}` | "Find outdoor venues in Bangalore for 5000" |
| Communities | `{name} {platform} {topics joined} {description}` | "Find AI communities on Discord" |

### 4.2 Embedding Model

**text-embedding-3-small** (OpenAI) or **voyage-3-lite** (Voyage AI)
- 1536 dimensions
- Cost-effective for hackathon scale
- High quality for similarity search

### 4.3 Pinecone Index Structure

```python
# Single index with namespace-based separation
index = pinecone.Index("srishti-events")

# Namespaces:
# - "events" — all event embeddings
# - "sponsors" — sponsor embeddings
# - "talents" — speaker/artist embeddings
# - "venues" — venue embeddings
# - "communities" — community embeddings

# Metadata filters enable precise queries
results = index.query(
    vector=query_embedding,
    top_k=20,
    namespace="sponsors",
    filter={
        "industry": {"$in": ["cloud", "ai", "saas"]},
        "country": {"$eq": "India"},
        "company_size": {"$in": ["mid", "enterprise"]}
    }
)
```

### 4.4 RAG Pipeline (per agent query)

```
Agent Query: "Find relevant AI sponsors in India with >$1M marketing budget"
    │
    ▼
┌─────────────────────┐
│ 1. Embed query       │  → [0.12, -0.45, 0.78, ...]
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Vector search     │  → Top 30 similar sponsors from Pinecone
│    (Pinecone)        │     with metadata filters (industry=AI, country=India)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. SQL enrichment    │  → Join with PostgreSQL for full structured data
│    (PostgreSQL)      │     (past sponsorships, exact budgets, contact info)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. LLM reasoning     │  → Claude/GPT scores and ranks candidates
│    with full context  │     using retrieved data as context
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. Structured output │  → JSON with scored, ranked sponsor list
└─────────────────────┘
```

---

## 5. Mandatory Data Deliverable Plan

### Requirement
> A structured dataset of conferences/music festivals/sporting events from 2025 and 2026 events. At least 50 events per category for primary domain. CSV/JSON format with all required fields.

### Collection Strategy

| Domain | Target Count | Primary Sources | Backup Sources |
|--------|-------------|----------------|----------------|
| **Conferences** | 100+ events | conf.tech, Eventbrite, Luma, 10times | Manual Google search |
| **Music Festivals** | 60+ events | Songkick, Festicket, JamBase | Wikipedia festival lists |
| **Sporting Events** | 60+ events | ESPN, Google Sports | Wikipedia sporting events |

### Required Fields (per PDF)

```json
{
  "event_name": "NeurIPS 2025",
  "dates": { "start": "2025-12-08", "end": "2025-12-13" },
  "location": { "city": "San Diego", "country": "USA" },
  "category": "AI/ML",
  "theme": "Machine Learning Research",
  "sponsors": ["Google", "Meta", "Microsoft", "NVIDIA"],
  "speakers": ["Yann LeCun", "Fei-Fei Li", "..."],
  "estimated_attendance": 16000,
  "ticket_price": { "min": 100, "max": 1500, "currency": "USD" },
  "website": "https://neurips.cc",
  "data_source": "neurips.cc + manual verification",
  "extraction_method": "playwright_scraper + manual"
}
```

### Deliverable Format

Two files per domain:
1. `data/conferences_2025_2026.csv` — flat CSV with all fields
2. `data/conferences_2025_2026.json` — rich JSON with nested structures

Plus a documentation file:
3. `data/DATA_SOURCES.md` — explains every source, extraction method, data quality notes

### Collection Timeline
- **Day 1-2**: Automated scraping of structured sources (conf.tech, Eventbrite, Songkick, ESPN)
- **Day 2-3**: Semi-automated extraction from event websites
- **Day 3-4**: Manual curation to fill gaps (sponsors, attendance estimates)
- **Day 4**: Deduplication, validation, quality checks
- **Day 4**: Generate CSV + JSON exports, write documentation

### Quality Assurance
- Every record must have: name, date, location, category (4 mandatory fields)
- At least 70% of records should have: sponsors, speakers, attendance estimate
- All extraction methods documented
- Deduplication by (event_name + year + city) composite key
- Human spot-check of 20% of records

---

## 6. Data Refresh Strategy (for demo)

For the hackathon prototype, we pre-populate the database with the mandatory dataset. During the demo:

1. **Static data**: Pre-loaded 220+ events from mandatory dataset
2. **Live scraping demo**: Show one agent performing a live search (e.g., "Find AI conferences in Europe 2026") that hits real APIs
3. **Cache layer**: Redis caches recent scraping results to avoid demo failures from rate limits

```python
# Redis caching for scraper results
async def cached_scrape(source: str, params: dict, ttl: int = 3600):
    cache_key = f"scrape:{source}:{hash(str(params))}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    result = await scraper.scrape(params)
    await redis.setex(cache_key, ttl, json.dumps(result))
    return result
```

---

## 7. Data Privacy & Ethics

- **No PII storage**: We store public professional data only (company names, public profiles)
- **Rate limiting**: All scrapers respect robots.txt and rate limits
- **Attribution**: Every data point links back to its source
- **No login-required scraping**: We don't scrape behind authentication walls
- **GDPR consideration**: Individuals can be excluded from recommendations on request

# Srishti Dataset — Sources & Methodology

**Last updated:** 2026-04-16
**Total events:** 241 (88 conferences, 130 music festivals, 23 sporting events)
**Time range:** 2025-2026

---

## 1. Collection Approach

We built the dataset using the scraping + live-tools pipeline described in `04_Data_Strategy.md` and `PHASES.md`:

- **Web scraping** of public event listing platforms for structured base records (name, dates, venue, pricing, website, description).
- **Custom web search tools built on Exa** for targeted freshness and verification — used to confirm sponsors, lineups, stadium capacities, and attendance figures for well-known events.

The output of both layers is merged into a single unified schema and exported as CSV + JSON per domain.

---

## 2. Data Sources

### Scraped (public event platforms)

| Source | Domain(s) | Notes |
|--------|----------|-------|
| **Devfolio** (`devfolio.co`) | conferences / hackathons | India-focused hackathon hub |
| **District** (`district.in`) | conferences, music, sports | Pan-India event discovery platform |
| **Mepass** (`mepass.in`) | conferences, music, sports | Ticketing + event listings |
| **Skillboxes** (`skillboxes.com`) | music festivals | Music-focused discovery |

### Live web search (Exa-based custom tools)

For globally-famous events (NeurIPS, CES, Coachella, FIFA World Cup 2026, IPL 2026, etc.) we used custom Exa-backed search tools to fetch verified facts from primary sources:

- Official event websites (neurips.cc, sunburn.in, fifa.com, formula1.com, etc.)
- Wikipedia event pages
- Sponsor announcement pages and official partner lists

Every curated event stores a `data_source` of `curated_web_research` and preserves its provenance in `raw_data`.

---

## 3. Unified Schema

Every event, regardless of source, is normalized to this schema:

```json
{
  "name": "string",
  "domain": "conference | music_festival | sporting_event",
  "category": "string",
  "subcategory": "string | null",
  "description": "string | null",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD | null",
  "city": "string | null",
  "country": "string | null",
  "venue_name": "string | null",
  "estimated_attendance": "int | null",
  "ticket_price_min": "float | null",
  "ticket_price_max": "float | null",
  "currency": "ISO-4217 code",
  "website_url": "url",
  "year": "int",
  "sponsors": ["string"],
  "speakers": ["string"],
  "data_source": "string",
  "extraction_method": "string",
  "raw_data": {}
}
```

---

## 4. Coverage Statistics

| Field | Conferences (88) | Music (130) | Sports (23) |
|-------|------------------|-------------|-------------|
| name | 100% | 100% | 100% |
| start_date | 100% | 100% | 100% |
| end_date | 100% | 100% | 100% |
| city + country | 98% | 99% | 100% |
| venue_name | 85% | 99% | 100% |
| estimated_attendance | 100% | 100% | 100% |
| ticket_price | 88% | 88% | 67% |
| website_url | 100% | 100% | 100% |
| sponsors | 25% | 7% | 70% |
| speakers / artists | 23% | 87% | 61% |

### Geographic diversity
- **Conferences:** India, USA, UK, Canada, Portugal (5 countries)
- **Music festivals:** India, USA, UK, Belgium (4 countries)
- **Sporting events:** India, USA, UK, Mexico, Hungary, Monaco (6 countries)

### Year distribution
- 2025: 13 events (historical anchor)
- 2026: 228 events (primary planning target)

---

## 5. Privacy & Ethics

- Only public, non-login-required data was collected.
- No personal/private information stored — only professional event metadata.
- All data points link back to their source via `website_url` and `data_source`.
- Scraping respected `robots.txt` and used conservative rate limits.

---

## 6. Known Limitations

1. **Geographic concentration in India.** The scraped source platforms are predominantly Indian; globally-famous events were added via curated web search to provide geographic diversity.
2. **Sponsor coverage is selective.** Small local events (college hackathons, club nights) rarely disclose sponsors publicly, so those fields are intentionally left empty rather than fabricated. Famous events with verified sponsor disclosures are richly populated.
3. **Attendance estimates vary in confidence.** Stadium and famous-festival numbers are high-confidence; local venue estimates are based on venue-type heuristics.

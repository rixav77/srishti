"""Sports scraper — Wikipedia infobox + wikitable CSS extraction. No LLM needed."""
import json
import logging
import re

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from ..base import BaseScraper
from ..normalize import make_event

logger = logging.getLogger(__name__)

STEALTH_BROWSER = BrowserConfig(
    headless=True, enable_stealth=True, user_agent_mode="random",
    viewport_width=1366, viewport_height=768,
)

# For single event pages: extract the infobox
INFOBOX_SCHEMA = {
    "name": "infobox",
    "baseSelector": "table.infobox",
    "fields": [
        {
            "name": "rows",
            "selector": "tr",
            "type": "nested_list",
            "fields": [
                {"name": "label", "selector": "th", "type": "text"},
                {"name": "value", "selector": "td", "type": "text"},
            ],
        }
    ],
}

# For list pages: extract wikitable rows (e.g. "2025 in tennis")
WIKITABLE_SCHEMA = {
    "name": "events",
    "baseSelector": "table.wikitable tbody tr",
    "fields": [
        {"name": "col0", "selector": "td:nth-child(1)", "type": "text"},
        {"name": "col1", "selector": "td:nth-child(2)", "type": "text"},
        {"name": "col2", "selector": "td:nth-child(3)", "type": "text"},
        {"name": "col3", "selector": "td:nth-child(4)", "type": "text"},
        {"name": "col4", "selector": "td:nth-child(5)", "type": "text"},
        {"name": "link",  "selector": "td a",           "type": "attribute", "attribute": "href"},
    ],
}

# List pages: (url, sport, [date_col, name_col, location_col])
# Column indices derived from inspecting the actual wikitable headers
LIST_PAGES = [
    ("https://en.wikipedia.org/wiki/2025_in_tennis",          "Tennis"),
    ("https://en.wikipedia.org/wiki/2025_in_cricket",         "Cricket"),
    ("https://en.wikipedia.org/wiki/2025_in_baseball",        "Baseball"),
    ("https://en.wikipedia.org/wiki/2025_in_American_football", "American Football"),
]

# Single event pages: (url, event_name, sport, city, country)
SINGLE_PAGES = [
    ("https://en.wikipedia.org/wiki/Super_Bowl_LIX",                       "Super Bowl LIX",              "American Football"),
    ("https://en.wikipedia.org/wiki/2025_NBA_Finals",                      "NBA Finals 2025",             "Basketball"),
    ("https://en.wikipedia.org/wiki/2025_Wimbledon_Championships",         "Wimbledon 2025",              "Tennis"),
    ("https://en.wikipedia.org/wiki/2025_ICC_Champions_Trophy",            "ICC Champions Trophy 2025",   "Cricket"),
    ("https://en.wikipedia.org/wiki/2025_Rugby_World_Cup",                 "Rugby World Cup 2025",        "Rugby"),
    ("https://en.wikipedia.org/wiki/2025_Formula_One_World_Championship",  "Formula One Season 2025",     "Motorsport"),
    ("https://en.wikipedia.org/wiki/2025_French_Open",                     "French Open 2025",            "Tennis"),
    ("https://en.wikipedia.org/wiki/2025_Australian_Open",                 "Australian Open 2025",        "Tennis"),
    ("https://en.wikipedia.org/wiki/2025_US_Open_(tennis)",                "US Open Tennis 2025",         "Tennis"),
    ("https://en.wikipedia.org/wiki/2025_Masters_Tournament",              "The Masters 2025",            "Golf"),
    ("https://en.wikipedia.org/wiki/2025_FIFA_Club_World_Cup",             "FIFA Club World Cup 2025",    "Football"),
    ("https://en.wikipedia.org/wiki/2025_NBA_All-Star_Game",               "NBA All-Star Game 2025",      "Basketball"),
    ("https://en.wikipedia.org/wiki/2025_NFL_Draft",                       "NFL Draft 2025",              "American Football"),
    ("https://en.wikipedia.org/wiki/2025_World_Athletics_Championships",   "World Athletics Champs 2025", "Athletics"),
    ("https://en.wikipedia.org/wiki/2025_Tour_de_France",                  "Tour de France 2025",         "Cycling"),
    ("https://en.wikipedia.org/wiki/2025_Boston_Marathon",                 "Boston Marathon 2025",        "Athletics"),
    ("https://en.wikipedia.org/wiki/2025_Daytona_500",                     "Daytona 500 2025",            "Motorsport"),
    ("https://en.wikipedia.org/wiki/2025_Kentucky_Derby",                  "Kentucky Derby 2025",         "Horse Racing"),
    ("https://en.wikipedia.org/wiki/2025_US_Open_(golf)",                  "US Open Golf 2025",           "Golf"),
    ("https://en.wikipedia.org/wiki/2025_The_Open_Championship",           "The Open Championship 2025",  "Golf"),
    ("https://en.wikipedia.org/wiki/2025_PGA_Championship",                "PGA Championship 2025",       "Golf"),
    ("https://en.wikipedia.org/wiki/2025_UEFA_Champions_League_Final",     "UEFA Champions League Final", "Football"),
    ("https://en.wikipedia.org/wiki/2025_Copa_Am%C3%A9rica",               "Copa America 2025",           "Football"),
    ("https://en.wikipedia.org/wiki/2025_Ryder_Cup",                       "Ryder Cup 2025",              "Golf"),
    ("https://en.wikipedia.org/wiki/2025_New_York_City_Marathon",          "NYC Marathon 2025",           "Athletics"),
    # Additional 2025 events
    ("https://en.wikipedia.org/wiki/2025_Stanley_Cup_Finals",              "Stanley Cup Finals 2025",     "Ice Hockey"),
    ("https://en.wikipedia.org/wiki/2025_Preakness_Stakes",                "Preakness Stakes 2025",       "Horse Racing"),
    ("https://en.wikipedia.org/wiki/2025_Belmont_Stakes",                  "Belmont Stakes 2025",         "Horse Racing"),
    ("https://en.wikipedia.org/wiki/2025_Indianapolis_500",                "Indianapolis 500 2025",       "Motorsport"),
    ("https://en.wikipedia.org/wiki/2025_Breeders%27_Cup",                 "Breeders' Cup 2025",          "Horse Racing"),
    ("https://en.wikipedia.org/wiki/2025_NBA_draft",                       "NBA Draft 2025",              "Basketball"),
    ("https://en.wikipedia.org/wiki/2025_MLB_All-Star_Game",               "MLB All-Star Game 2025",      "Baseball"),
    ("https://en.wikipedia.org/wiki/2025_World_Series",                    "World Series 2025",           "Baseball"),
    ("https://en.wikipedia.org/wiki/2025_Super_Rugby_Pacific_season",      "Super Rugby Pacific 2025",    "Rugby"),
    ("https://en.wikipedia.org/wiki/2025_Six_Nations_Championship",        "Six Nations 2025",            "Rugby"),
    ("https://en.wikipedia.org/wiki/2025_Indian_Premier_League",           "IPL 2025",                    "Cricket"),
    ("https://en.wikipedia.org/wiki/2025_Ashes_series",                    "The Ashes 2025",              "Cricket"),
    ("https://en.wikipedia.org/wiki/2025_FIFA_Women%27s_World_Cup",        "FIFA Women's World Cup 2025", "Football"),
    ("https://en.wikipedia.org/wiki/2025_CONCACAF_Gold_Cup",               "CONCACAF Gold Cup 2025",      "Football"),
    ("https://en.wikipedia.org/wiki/2025_Africa_Cup_of_Nations",           "Africa Cup of Nations 2025",  "Football"),
    ("https://en.wikipedia.org/wiki/2025_Chicago_Marathon",                "Chicago Marathon 2025",       "Athletics"),
    ("https://en.wikipedia.org/wiki/2025_London_Marathon",                 "London Marathon 2025",        "Athletics"),
    ("https://en.wikipedia.org/wiki/2025_Berlin_Marathon",                 "Berlin Marathon 2025",        "Athletics"),
    ("https://en.wikipedia.org/wiki/2025_Monaco_Grand_Prix",               "Monaco Grand Prix 2025",      "Motorsport"),
    ("https://en.wikipedia.org/wiki/2025_British_Grand_Prix",              "British Grand Prix 2025",     "Motorsport"),
    ("https://en.wikipedia.org/wiki/2025_Italian_Grand_Prix",              "Italian Grand Prix 2025",     "Motorsport"),
    ("https://en.wikipedia.org/wiki/2025_24_Hours_of_Le_Mans",             "24 Hours of Le Mans 2025",    "Motorsport"),
    ("https://en.wikipedia.org/wiki/2025_Vuelta_a_Espa%C3%B1a",           "Vuelta a España 2025",        "Cycling"),
    ("https://en.wikipedia.org/wiki/2025_Giro_d%27Italia",                 "Giro d'Italia 2025",          "Cycling"),
    ("https://en.wikipedia.org/wiki/2025_US_Open_(tennis)",                "US Open Tennis 2025",         "Tennis"),
    ("https://en.wikipedia.org/wiki/2025_Indian_Wells_Masters",            "Indian Wells Masters 2025",   "Tennis"),
    ("https://en.wikipedia.org/wiki/2025_Miami_Open",                      "Miami Open 2025",             "Tennis"),
    ("https://en.wikipedia.org/wiki/2025_Roland_Garros",                   "Roland Garros 2025",          "Tennis"),
    ("https://en.wikipedia.org/wiki/2025_Nitto_ATP_Finals",                "ATP Finals 2025",             "Tennis"),
    ("https://en.wikipedia.org/wiki/2025_Davis_Cup_Finals",                "Davis Cup Finals 2025",       "Tennis"),
    ("https://en.wikipedia.org/wiki/2025_NBA_In-Season_Tournament",        "NBA In-Season Tournament 2025","Basketball"),
    ("https://en.wikipedia.org/wiki/2025_UEFA_Europa_League_Final",        "UEFA Europa League Final 2025","Football"),
    ("https://en.wikipedia.org/wiki/2025_FA_Cup_Final",                    "FA Cup Final 2025",           "Football"),
]


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_infobox(rows: list[dict]) -> dict:
    parsed = {}
    for row in rows:
        label = (row.get("label") or "").strip().lower()
        value = (row.get("value") or "").strip()
        if label and value:
            parsed[label] = value
    return parsed


_MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}
_MONTH_PAT = (
    "january|february|march|april|may|june|july|august"
    "|september|october|november|december"
)


def _extract_date(text: str) -> str | None:
    if not text:
        return None
    # ISO date
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    # Month Day, Year
    m2 = re.search(
        rf"({_MONTH_PAT})\s+(\d{{1,2}})[^,\d]*,?\s*(20\d{{2}})", text, re.I
    )
    if m2:
        return f"{m2.group(3)}-{_MONTHS[m2.group(1).lower()]}-{m2.group(2).zfill(2)}"
    # Month Year
    m3 = re.search(rf"({_MONTH_PAT})\s+(20\d{{2}})", text, re.I)
    if m3:
        return f"{m3.group(2)}-{_MONTHS[m3.group(1).lower()]}-01"
    # Year only
    m4 = re.search(r"(202[4-9])", text)
    if m4:
        mon = re.search(rf"({_MONTH_PAT})", text, re.I)
        if mon:
            return f"{m4.group(1)}-{_MONTHS[mon.group(1).lower()]}-01"
        return f"{m4.group(1)}-01-01"
    return None


def _extract_attendance(text: str) -> int | None:
    if not text:
        return None
    # Normalise European thousands separators: "130.000" → "130000"
    text = re.sub(r"(\d)\.(\d{3})(?!\d)", r"\1\2", text)
    text = text.replace(",", "")
    m = re.search(r"(\d+)", text)
    try:
        return int(m.group(1)) if m else None
    except (ValueError, AttributeError):
        return None


def _clean_location(text: str) -> str:
    """Extract the city/country portion from a Wikipedia infobox location string."""
    if not text:
        return ""
    text = re.sub(r"\d+°\d+[′'″]\s*[NSEW]\s*\d+°\d+[′'″]\s*[NSEW].*", "", text)
    text = re.sub(r"\d+\.\d+[;°].*", "", text)
    text = re.sub(r"[\ufeff\u200b\u200c\u200d]", "", text)
    # Prefer parenthetical location (e.g. "Venue(City, Country)")
    parens = re.findall(r"\(([^()]+)\)", text)
    for p in parens:
        if "," in p and len(p) < 80:
            text = p
            break
    else:
        text = re.sub(r"\[.*?\]|\(.*?\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if "," not in text:
        return text
    parts = [p.strip() for p in text.split(",") if p.strip()]
    venue_words = {"park", "club", "center", "centre", "arena", "stadium",
                   "field", "grounds", "fairground", "island", "campus",
                   "polo", "expo", "pavilion", "gardens", "manor", "estate",
                   "bowl", "dome", "coliseum", "colosseum", "speedway"}
    first_city_idx = 0
    for i, part in enumerate(parts):
        words = set(part.lower().split())
        if words & venue_words:
            first_city_idx = i + 1
        else:
            break
    return ", ".join(parts[first_city_idx:])


def _parse_location(text: str) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    text = _clean_location(text)
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) >= 3:
        # "City, State, Country" — use first as city, last as country
        return parts[0], parts[-1]
    if len(parts) == 2:
        return parts[0], parts[1]
    return text.strip(), None


# ── scraper ───────────────────────────────────────────────────────────────────

class WikipediaSportsScraper(BaseScraper):
    source_name = "wikipedia_sports"
    max_concurrent = 5

    async def scrape(self, **kwargs) -> list[dict]:
        raw_events = []

        infobox_config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(schema=INFOBOX_SCHEMA),
            cache_mode=CacheMode.BYPASS,
            magic=True, simulate_user=True, override_navigator=True,
            # No css_selector — let baseSelector in the schema handle it
            excluded_tags=["nav", "footer", "script", "style"],
            page_timeout=30000,
        )

        wikitable_config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(schema=WIKITABLE_SCHEMA),
            cache_mode=CacheMode.BYPASS,
            magic=True, simulate_user=True, override_navigator=True,
            # No css_selector — let baseSelector in the schema handle it
            excluded_tags=["nav", "footer", "script", "style"],
            page_timeout=45000,
        )

        async with AsyncWebCrawler(config=STEALTH_BROWSER) as crawler:
            # --- List pages (wikitable rows) ---
            for url, sport in LIST_PAGES:
                result = await crawler.arun(url, config=wikitable_config)
                if not result.success or not result.extracted_content:
                    logger.warning(f"[{self.source_name}] No wikitable: {sport}")
                    continue
                try:
                    rows = json.loads(result.extracted_content)
                    for row in (rows if isinstance(rows, list) else []):
                        row["_sport"] = sport
                        row["_mode"] = "list"
                        row["_source_url"] = url
                    raw_events.extend(rows if isinstance(rows, list) else [])
                    logger.info(f"[{self.source_name}] {sport} list → {len(rows)} rows")
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"[{self.source_name}] Parse error: {sport}")

            # --- Single event pages (infobox) ---
            # Build url→(label, sport) map — arun_many does NOT guarantee result order
            single_meta: dict[str, tuple[str, str]] = {
                url: (label, sport) for url, label, sport in SINGLE_PAGES
            }

            for i in range(0, len(SINGLE_PAGES), self.max_concurrent):
                batch = SINGLE_PAGES[i: i + self.max_concurrent]
                urls = [u for u, _, _ in batch]
                results = await crawler.arun_many(urls, config=infobox_config, max_concurrent=self.max_concurrent)

                for result in results:
                    result_url = getattr(result, "url", None) or getattr(result, "request_url", None)
                    meta = single_meta.get(result_url) if result_url else None
                    if meta is None:
                        for u in urls:
                            if result_url and u.rstrip("/") == result_url.rstrip("/"):
                                meta = single_meta.get(u)
                                result_url = u
                                break
                    if meta is None:
                        logger.warning(f"[{self.source_name}] Cannot match result URL: {result_url}")
                        continue
                    label, sport = meta

                    if not result.success or not result.extracted_content:
                        logger.warning(f"[{self.source_name}] No infobox: {label}")
                        raw_events.append({"_label": label, "_sport": sport, "_url": result_url, "_mode": "single", "rows": []})
                        continue
                    try:
                        data = json.loads(result.extracted_content)
                        entry = data[0] if isinstance(data, list) and data else {}
                        entry["_label"] = label
                        entry["_sport"] = sport
                        entry["_url"] = result_url
                        entry["_mode"] = "single"
                        raw_events.append(entry)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"[{self.source_name}] Parse error: {label}")

        return raw_events

    def normalize(self, raw: dict) -> dict | None:
        mode = raw.get("_mode")

        if mode == "single":
            return self._normalize_single(raw)
        elif mode == "list":
            return self._normalize_list_row(raw)
        return None

    def _normalize_single(self, raw: dict) -> dict | None:
        rows = raw.get("rows") or []
        info = _parse_infobox(rows)
        label = raw.get("_label", "")

        name = info.get("name") or info.get("event") or label
        if not name:
            return None

        date_text = (info.get("date") or info.get("dates") or
                     info.get("tournament dates") or info.get("season") or "")
        start_date = _extract_date(date_text)

        location_text = (info.get("location") or info.get("locations")
                         or info.get("venue") or "")
        city, country = _parse_location(location_text)

        return make_event(
            name=name,
            domain="sporting_event",
            category=raw.get("_sport", "Sports"),
            start_date=start_date,
            city=city,
            country=country,
            venue_name=info.get("venue") or info.get("stadium"),
            estimated_attendance=_extract_attendance(info.get("attendance") or ""),
            website_url=info.get("website") or raw.get("_url"),
            data_source="wikipedia",
            extraction_method="crawl4ai_css_infobox",
            raw_data=info,
        )

    def _normalize_list_row(self, raw: dict) -> dict | None:
        # Wikitable rows: col0..col4 contain date, name, category, location etc.
        # Column order varies by sport — use heuristics
        cols = [
            (raw.get("col0") or "").strip(),
            (raw.get("col1") or "").strip(),
            (raw.get("col2") or "").strip(),
            (raw.get("col3") or "").strip(),
            (raw.get("col4") or "").strip(),
        ]
        # Skip header rows (all empty or no date-like content)
        if not any(cols):
            return None

        sport = raw.get("_sport", "Sports")

        # Try to identify name column: longest non-date text
        date_col = next((i for i, c in enumerate(cols) if _extract_date(c)), None)
        name_col = next(
            (i for i, c in enumerate(cols)
             if c and i != date_col and len(c) > 5 and not c.isdigit()),
            None
        )

        name = cols[name_col] if name_col is not None else None
        if not name:
            return None

        start_date = _extract_date(cols[date_col]) if date_col is not None else None

        # Location: look for comma-separated value that looks like a city
        location_col = next(
            (i for i, c in enumerate(cols)
             if "," in c and i != date_col and i != name_col),
            None
        )
        city, country = _parse_location(cols[location_col]) if location_col is not None else (None, None)

        return make_event(
            name=f"{name} ({sport})" if sport not in name else name,
            domain="sporting_event",
            category=sport,
            start_date=start_date,
            city=city,
            country=country,
            website_url=raw.get("_source_url"),
            data_source="wikipedia",
            extraction_method="crawl4ai_css_wikitable",
            raw_data={k: v for k, v in raw.items() if not k.startswith("_")},
        )

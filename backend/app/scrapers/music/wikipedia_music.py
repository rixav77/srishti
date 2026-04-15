"""Music festival scraper — Wikipedia infobox CSS extraction. No LLM needed."""
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

# Wikipedia infobox: each row is <tr><th>Label</th><td>Value</td></tr>
# We extract all rows then parse by label in normalize()
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

# Curated list of major festivals with Wikipedia pages
FESTIVAL_PAGES = [
    ("https://en.wikipedia.org/wiki/Coachella_Valley_Music_and_Arts_Festival", "Coachella", "USA"),
    ("https://en.wikipedia.org/wiki/Glastonbury_Festival",                     "Glastonbury", "UK"),
    ("https://en.wikipedia.org/wiki/Lollapalooza",                             "Lollapalooza", "USA"),
    ("https://en.wikipedia.org/wiki/Bonnaroo_Music_and_Arts_Festival",         "Bonnaroo", "USA"),
    ("https://en.wikipedia.org/wiki/Tomorrowland_(festival)",                  "Tomorrowland", "Belgium"),
    ("https://en.wikipedia.org/wiki/Ultra_Music_Festival",                     "Ultra Music Festival", "USA"),
    ("https://en.wikipedia.org/wiki/Electric_Daisy_Carnival",                  "Electric Daisy Carnival", "USA"),
    ("https://en.wikipedia.org/wiki/Outside_Lands_Music_and_Arts_Festival",    "Outside Lands", "USA"),
    ("https://en.wikipedia.org/wiki/Austin_City_Limits_Music_Festival",        "Austin City Limits", "USA"),
    ("https://en.wikipedia.org/wiki/Burning_Man",                              "Burning Man", "USA"),
    ("https://en.wikipedia.org/wiki/Primavera_Sound",                          "Primavera Sound", "Spain"),
    ("https://en.wikipedia.org/wiki/Rock_in_Rio",                              "Rock in Rio", "Brazil"),
    ("https://en.wikipedia.org/wiki/Download_Festival",                        "Download Festival", "UK"),
    ("https://en.wikipedia.org/wiki/Reading_and_Leeds_Festivals",              "Reading & Leeds", "UK"),
    ("https://en.wikipedia.org/wiki/Electric_Forest_Festival",                 "Electric Forest", "USA"),
    ("https://en.wikipedia.org/wiki/Pitchfork_Music_Festival",                 "Pitchfork Festival", "USA"),
    ("https://en.wikipedia.org/wiki/New_Orleans_Jazz_%26_Heritage_Festival",   "New Orleans Jazz Fest", "USA"),
    ("https://en.wikipedia.org/wiki/Governors_Ball_Music_Festival",            "Governors Ball", "USA"),
    ("https://en.wikipedia.org/wiki/Osheaga_Music_and_Arts_Festival",          "Osheaga", "Canada"),
    ("https://en.wikipedia.org/wiki/Roskilde_Festival",                        "Roskilde Festival", "Denmark"),
    ("https://en.wikipedia.org/wiki/Wacken_Open_Air",                          "Wacken Open Air", "Germany"),
    ("https://en.wikipedia.org/wiki/Sziget_Festival",                          "Sziget Festival", "Hungary"),
    ("https://en.wikipedia.org/wiki/Fuji_Rock_Festival",                       "Fuji Rock Festival", "Japan"),
    ("https://en.wikipedia.org/wiki/Summer_Sonic",                             "Summer Sonic", "Japan"),
    ("https://en.wikipedia.org/wiki/Rolling_Loud",                             "Rolling Loud", "USA"),
    ("https://en.wikipedia.org/wiki/Wireless_Festival",                        "Wireless Festival", "UK"),
    ("https://en.wikipedia.org/wiki/Southside_Festival",                       "Southside Festival", "Germany"),
    ("https://en.wikipedia.org/wiki/Rock_Werchter",                            "Rock Werchter", "Belgium"),
    ("https://en.wikipedia.org/wiki/Pinkpop",                                  "Pinkpop", "Netherlands"),
    ("https://en.wikipedia.org/wiki/Montr%C3%A9al_Jazz_Festival",              "Montreal Jazz Festival", "Canada"),
    ("https://en.wikipedia.org/wiki/North_Sea_Jazz_Festival",                  "North Sea Jazz", "Netherlands"),
    ("https://en.wikipedia.org/wiki/Sunburn_(festival)",                       "Sunburn Festival", "India"),
    ("https://en.wikipedia.org/wiki/NH7_Weekender",                            "NH7 Weekender", "India"),
    ("https://en.wikipedia.org/wiki/WOMAD",                                    "WOMAD", "UK"),
    ("https://en.wikipedia.org/wiki/Essence_Festival",                         "Essence Festival", "USA"),
    ("https://en.wikipedia.org/wiki/Forecastle_Festival",                      "Forecastle Festival", "USA"),
    ("https://en.wikipedia.org/wiki/Benicassim",                               "FIB Benicassim", "Spain"),
    ("https://en.wikipedia.org/wiki/Mad_Cool_Festival",                        "Mad Cool Festival", "Spain"),
    ("https://en.wikipedia.org/wiki/NOS_Alive",                                "NOS Alive", "Portugal"),
    ("https://en.wikipedia.org/wiki/Flow_Festival",                            "Flow Festival", "Finland"),
    ("https://en.wikipedia.org/wiki/Way_Out_West_(festival)",                  "Way Out West", "Sweden"),
    ("https://en.wikipedia.org/wiki/Bestival",                                 "Bestival", "UK"),
    ("https://en.wikipedia.org/wiki/Isle_of_Wight_Festival",                   "Isle of Wight Festival", "UK"),
    ("https://en.wikipedia.org/wiki/Lollapalooza_Brasil",                      "Lollapalooza Brasil", "Brazil"),
    ("https://en.wikipedia.org/wiki/Lollapalooza_Argentina",                   "Lollapalooza Argentina", "Argentina"),
    ("https://en.wikipedia.org/wiki/Lollapalooza_Chile",                       "Lollapalooza Chile", "Chile"),
    ("https://en.wikipedia.org/wiki/Aftershock_Festival",                      "Aftershock Festival", "USA"),
    ("https://en.wikipedia.org/wiki/Riot_Fest",                                "Riot Fest", "USA"),
    ("https://en.wikipedia.org/wiki/Firefly_Music_Festival",                   "Firefly Music Festival", "USA"),
    ("https://en.wikipedia.org/wiki/Splendour_in_the_Grass",                   "Splendour in the Grass", "Australia"),
    ("https://en.wikipedia.org/wiki/Mawazine",                                 "Mawazine Festival", "Morocco"),
    ("https://en.wikipedia.org/wiki/Parklife_Festival",                        "Parklife Festival", "UK"),
    ("https://en.wikipedia.org/wiki/Pitchfork_Music_Festival_Paris",           "Pitchfork Paris", "France"),
    ("https://en.wikipedia.org/wiki/Made_in_America_(music_festival)",         "Made in America", "USA"),
    ("https://en.wikipedia.org/wiki/Hard_Summer",                              "Hard Summer", "USA"),
    ("https://en.wikipedia.org/wiki/We_Are_FSTVL",                             "We Are FSTVL", "UK"),
    ("https://en.wikipedia.org/wiki/Hay_Festival",                             "Hay Festival", "UK"),
    ("https://en.wikipedia.org/wiki/Panorama_Music_Festival",                  "Panorama Festival", "USA"),
    ("https://en.wikipedia.org/wiki/Lollapalooza_Paris",                       "Lollapalooza Paris", "France"),
    ("https://en.wikipedia.org/wiki/Lollapalooza_Germany",                     "Lollapalooza Germany", "Germany"),
    ("https://en.wikipedia.org/wiki/Lollapalooza_Sweden",                      "Lollapalooza Sweden", "Sweden"),
    ("https://en.wikipedia.org/wiki/Beyond_Wonderland",                        "Beyond Wonderland", "USA"),
    ("https://en.wikipedia.org/wiki/Electric_Zoo",                             "Electric Zoo", "USA"),
    ("https://en.wikipedia.org/wiki/Mysteryland",                              "Mysteryland", "Netherlands"),
    ("https://en.wikipedia.org/wiki/Creamfields",                              "Creamfields", "UK"),
    ("https://en.wikipedia.org/wiki/Global_Gathering",                         "Global Gathering", "UK"),
    # Additional festivals — specific 2025 editions (have dedicated pages with dates)
    ("https://en.wikipedia.org/wiki/2025_Coachella_Valley_Music_and_Arts_Festival", "Coachella 2025", "USA"),
    ("https://en.wikipedia.org/wiki/2025_Glastonbury_Festival",                 "Glastonbury 2025", "UK"),
    ("https://en.wikipedia.org/wiki/Hurricane_Festival",                        "Hurricane Festival", "Germany"),
    ("https://en.wikipedia.org/wiki/Hellfest_(festival)",                       "Hellfest", "France"),
    ("https://en.wikipedia.org/wiki/Pukkelpop",                                 "Pukkelpop", "Belgium"),
    ("https://en.wikipedia.org/wiki/Untold_Festival",                           "Untold Festival", "Romania"),
    ("https://en.wikipedia.org/wiki/Exit_festival",                             "Exit Festival", "Serbia"),
    ("https://en.wikipedia.org/wiki/Neon_Gold_Festival",                        "Neon Gold Festival", "USA"),
    ("https://en.wikipedia.org/wiki/Lollapalooza_S%C3%A3o_Paulo_2025",          "Lollapalooza São Paulo 2025", "Brazil"),
    ("https://en.wikipedia.org/wiki/Summerfest",                                "Summerfest", "USA"),
    ("https://en.wikipedia.org/wiki/Newport_Folk_Festival",                     "Newport Folk Festival", "USA"),
    ("https://en.wikipedia.org/wiki/Newport_Jazz_Festival",                     "Newport Jazz Festival", "USA"),
    ("https://en.wikipedia.org/wiki/Lollapalooza_Chicago_2025",                 "Lollapalooza Chicago 2025", "USA"),
    ("https://en.wikipedia.org/wiki/Osheaga_Music_and_Arts_Festival_2025",      "Osheaga 2025", "Canada"),
    ("https://en.wikipedia.org/wiki/Knotfest",                                  "Knotfest", "USA"),
    ("https://en.wikipedia.org/wiki/Vans_Warped_Tour",                          "Warped Tour", "USA"),
    ("https://en.wikipedia.org/wiki/Sasquatch!_Music_Festival",                 "Sasquatch Festival", "USA"),
    ("https://en.wikipedia.org/wiki/Rocklahoma",                                "Rocklahoma", "USA"),
    ("https://en.wikipedia.org/wiki/Sea.Hear.Now",                              "Sea.Hear.Now", "USA"),
    ("https://en.wikipedia.org/wiki/Lockn%27_Festival",                         "Lockn' Festival", "USA"),
    ("https://en.wikipedia.org/wiki/Stagecoach_Festival",                       "Stagecoach Festival", "USA"),
    ("https://en.wikipedia.org/wiki/BottleRock_Napa_Valley",                    "BottleRock Napa", "USA"),
    ("https://en.wikipedia.org/wiki/Lollapalooza_Chile_2025",                   "Lollapalooza Chile 2025", "Chile"),
    ("https://en.wikipedia.org/wiki/Lollapalooza_Argentina_2025",               "Lollapalooza Argentina 2025", "Argentina"),
]


def _parse_infobox(rows: list[dict]) -> dict:
    """Convert infobox rows list into a flat label→value dict, lowercased labels."""
    parsed = {}
    for row in rows:
        label = (row.get("label") or "").strip().lower()
        value = (row.get("value") or "").strip()
        if label and value:
            parsed[label] = value
    return parsed


def _clean_location(text: str) -> str:
    """Extract the city/country portion from a Wikipedia infobox location string.

    Strategy:
    1. If there's a parenthetical with a comma (e.g. "Venue(City, Country)"), use it.
    2. Otherwise strip parens and clean noise.
    3. Remove leading venue-name parts before the first place-name.
    """
    if not text:
        return ""
    # Remove coordinates and numeric noise first
    text = re.sub(r"\d+°\d+[′'″]\s*[NSEW]\s*\d+°\d+[′'″]\s*[NSEW].*", "", text)
    text = re.sub(r"\d+\.\d+[;°].*", "", text)
    text = re.sub(r"[\ufeff\u200b\u200c\u200d]", "", text)

    # If there's a useful parenthetical (e.g. "Empire Polo Club(Indio, California, U.S.)")
    # prefer the content inside the parens as it's usually the clean location
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

    # Drop leading venue-like tokens (e.g. "Grant Park, Chicago, IL" → keep all)
    parts = [p.strip() for p in text.split(",") if p.strip()]
    venue_words = {"park", "club", "center", "centre", "arena", "stadium",
                   "field", "grounds", "fairground", "island", "campus",
                   "polo", "expo", "pavilion", "gardens", "manor", "estate"}
    first_city_idx = 0
    for i, part in enumerate(parts):
        words = set(part.lower().split())
        if words & venue_words:
            first_city_idx = i + 1
        else:
            break
    return ", ".join(parts[first_city_idx:])


def _extract_attendance(text: str) -> int | None:
    if not text:
        return None
    # Normalise European thousands separators: "130.000" → "130000", "352.000" → "352000"
    # but not decimals like "1.5" (only convert if 3 digits follow the dot)
    text = re.sub(r"(\d)\.(\d{3})(?!\d)", r"\1\2", text)
    # Remove commas used as thousands separators
    text = text.replace(",", "")
    m = re.search(r"(\d+)", text)
    try:
        return int(m.group(1)) if m else None
    except (ValueError, AttributeError):
        return None


_MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}
_MONTH_PAT = (
    "january|february|march|april|may|june|july|august"
    "|september|october|november|december"
)


def _extract_year_from_date(text: str) -> str | None:
    """Return YYYY-MM-DD from date text, falling back to month or year approximation.

    Handles:
    - "June 27 – July 6, 2025"           → "2025-06-27"
    - "Two weekends in April and May"     → "2025-04-01"  (first month, current year)
    - "annually in June"                  → "2025-06-01"
    - "2025"                              → "2025-01-01"
    """
    if not text:
        return None

    # 1. Direct ISO date
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)

    # 2. "Month Day[–Day], Year"  e.g. "June 27 – July 6, 2025"
    m2 = re.search(
        rf"({_MONTH_PAT})\s+(\d{{1,2}})[^,\d]*,?\s*(20\d{{2}})", text, re.I
    )
    if m2:
        return f"{m2.group(3)}-{_MONTHS[m2.group(1).lower()]}-{m2.group(2).zfill(2)}"

    # 3. "Month Year"  e.g. "April 2025"
    m3 = re.search(rf"({_MONTH_PAT})\s+(20\d{{2}})", text, re.I)
    if m3:
        return f"{m3.group(2)}-{_MONTHS[m3.group(1).lower()]}-01"

    # 4. Year alone
    yr = re.search(r"(202[4-9])", text)
    if yr:
        # Try to find a month anywhere in the text even if no explicit year next to it
        mon = re.search(rf"({_MONTH_PAT})", text, re.I)
        if mon:
            return f"{yr.group(1)}-{_MONTHS[mon.group(1).lower()]}-01"
        return f"{yr.group(1)}-01-01"

    # 5. Month alone (no year) — descriptions like "annually in June"
    mon = re.search(rf"({_MONTH_PAT})", text, re.I)
    if mon:
        return f"2025-{_MONTHS[mon.group(1).lower()]}-01"

    return None


class WikipediaMusicScraper(BaseScraper):
    source_name = "wikipedia_music"
    max_concurrent = 5

    async def scrape(self, **kwargs) -> list[dict]:
        config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(schema=INFOBOX_SCHEMA),
            cache_mode=CacheMode.BYPASS,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            # Do NOT set css_selector here — it strips the page to that element
            # before JsonCssExtractionStrategy runs, so baseSelector can't match.
            # Let the full HTML through; baseSelector handles selection.
            excluded_tags=["nav", "footer", "script", "style"],
            page_timeout=30000,
        )

        raw_events = []
        # Build a url → (label, country) lookup so we can match by result.url
        # (arun_many does NOT guarantee result ordering matches input order)
        url_meta: dict[str, tuple[str, str]] = {
            url: (label, country) for url, label, country in FESTIVAL_PAGES
        }

        async with AsyncWebCrawler(config=STEALTH_BROWSER) as crawler:
            for i in range(0, len(FESTIVAL_PAGES), self.max_concurrent):
                batch = FESTIVAL_PAGES[i: i + self.max_concurrent]
                urls = [url for url, _, _ in batch]
                results = await crawler.arun_many(urls, config=config, max_concurrent=self.max_concurrent)

                for result in results:
                    # Match by the URL the crawler actually fetched
                    result_url = getattr(result, "url", None) or getattr(result, "request_url", None)
                    meta = url_meta.get(result_url) if result_url else None
                    if meta is None:
                        # Fallback: try stripping trailing slash / fragment
                        for u in urls:
                            if result_url and (result_url.rstrip("/") == u.rstrip("/") or u in (result_url or "")):
                                meta = url_meta.get(u)
                                result_url = u
                                break
                    if meta is None:
                        logger.warning(f"[{self.source_name}] Cannot match result URL: {result_url}")
                        continue
                    label, country = meta

                    if not result.success or not result.extracted_content:
                        logger.warning(f"[{self.source_name}] No infobox: {label}")
                        raw_events.append({"_label": label, "_country": country, "_url": result_url, "rows": []})
                        continue
                    try:
                        data = json.loads(result.extracted_content)
                        entry = data[0] if isinstance(data, list) and data else {}
                        entry["_label"] = label
                        entry["_country"] = country
                        entry["_url"] = result_url
                        raw_events.append(entry)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"[{self.source_name}] Parse error: {label}")
                        raw_events.append({"_label": label, "_country": country, "_url": result_url, "rows": []})

        return raw_events

    def normalize(self, raw: dict) -> dict | None:
        label = raw.get("_label", "")
        rows = raw.get("rows") or []
        info = _parse_infobox(rows)

        name = info.get("name") or label
        if not name:
            return None

        # Date: look for "dates", "date", "next event", "most recent"
        date_text = info.get("dates") or info.get("date") or info.get("next event") or ""
        start_date = _extract_year_from_date(date_text)

        # Location — infoboxes use "location", "locations", or "venue"
        location = (info.get("location") or info.get("locations")
                    or info.get("venue") or "")
        city = None
        country = raw.get("_country")  # fallback country from FESTIVAL_PAGES

        if location:
            cleaned = _clean_location(location)
            parts = [p.strip() for p in cleaned.split(",") if p.strip()]
            if len(parts) >= 3:
                # "City, State, Country" — city is first, country is last
                city = parts[0]
                country = parts[-1]
            elif len(parts) == 2:
                city = parts[0]
                country = parts[1]
            elif len(parts) == 1:
                city = parts[0]
            # Sanity check — drop clearly junk values
            if city and len(city) > 50:
                city = None

        genre = info.get("genre") or info.get("genres") or "Music"
        attendance = _extract_attendance(info.get("attendance") or info.get("capacity") or "")
        website = info.get("website") or raw.get("_url")

        return make_event(
            name=name,
            domain="music_festival",
            category=genre[:100] if genre else "Music",
            start_date=start_date,
            city=city,
            country=country,
            venue_name=info.get("venue") or info.get("location"),
            estimated_attendance=attendance,
            website_url=website,
            data_source="wikipedia",
            extraction_method="crawl4ai_css_infobox",
            raw_data={k: v for k, v in info.items()},
        )

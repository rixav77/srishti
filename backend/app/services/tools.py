"""Live tools layer — Tier 2 knowledge for agents.

All agents start with Tier 1 (Pinecone + Supabase).
When they need current/fresh data they call these tools.

Available tools
---------------
search_web(query, num_results)   — Exa neural search, Redis-cached 1h
scrape_page(url)                 — Playwright page fetch + markdown
get_company_info(name)           — Exa company search
get_artist_stats(name)           — Exa music/artist search

Groq tool schemas
-----------------
TOOL_SCHEMAS  — list of dicts in Groq function-calling format,
                 ready to pass as `tools=TOOL_SCHEMAS` to the Groq client.
"""

from __future__ import annotations

import hashlib
import json
import logging
from functools import lru_cache
from typing import Any

import redis as redis_lib

from app.config import get_settings

logger = logging.getLogger(__name__)


# ── clients ───────────────────────────────────────────────────────────────────

_exa_client = None


def _exa():
    """Create Exa client lazily so missing optional dependency doesn't crash runtime."""
    global _exa_client

    if _exa_client is not None:
        return _exa_client

    try:
        from exa_py import Exa  # type: ignore
    except Exception as exc:
        logger.warning(f"Exa client unavailable: {exc}")
        return None

    api_key = get_settings().exa_api_key
    if not api_key:
        logger.warning("EXA_API_KEY is not configured — live web search disabled")
        return None

    _exa_client = Exa(api_key=api_key)
    return _exa_client

@lru_cache(maxsize=1)
def _redis() -> redis_lib.Redis | None:
    try:
        url = get_settings().redis_url
        client = redis_lib.from_url(url, decode_responses=True, socket_timeout=5)
        client.ping()
        return client
    except Exception as exc:
        logger.warning(f"Redis unavailable — caching disabled: {exc}")
        return None


# ── cache helpers ─────────────────────────────────────────────────────────────

def _cache_key(prefix: str, payload: str) -> str:
    h = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"srishti:{prefix}:{h}"


def _cache_get(key: str) -> Any | None:
    r = _redis()
    if not r:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def _cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    r = _redis()
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.debug(f"Cache set failed: {exc}")


# ── tool implementations ───────────────────────────────────────────────────────

def search_web(query: str, num_results: int = 3) -> list[dict]:
    """
    Neural web search via Exa. Returns list of {title, url, snippet, published_date}.
    Results cached for 1 hour in Redis.
    """
    key = _cache_key("web", f"{query}:{num_results}")
    cached = _cache_get(key)
    if cached is not None:
        logger.debug(f"Cache hit: search_web({query!r})")
        return cached

    try:
        exa_client = _exa()
        if exa_client is None:
            return []

        response = exa_client.search_and_contents(
            query,
            num_results=num_results,
            type="neural",
            text={"max_characters": 800},
        )
        results = [
            {
                "title":          r.title or "",
                "url":            r.url or "",
                "snippet":        (r.text or "")[:800],
                "published_date": r.published_date or "",
            }
            for r in response.results
        ]
    except Exception as exc:
        logger.warning(f"search_web error: {exc}")
        results = []

    _cache_set(key, results)
    return results


def scrape_page(url: str) -> str:
    """
    Fetch a page and return clean markdown text via crawl4ai.
    Cached for 1 hour. Falls back to empty string on error.
    """
    key = _cache_key("page", url)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

        async def _fetch() -> str:
            cfg = BrowserConfig(headless=True, enable_stealth=True)
            run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=20000)
            async with AsyncWebCrawler(config=cfg) as crawler:
                result = await crawler.arun(url, config=run_cfg)
                return (result.markdown or "")[:3000] if result.success else ""

        # Works both inside and outside a running event loop
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, _fetch())
                text = future.result(timeout=30)
        except RuntimeError:
            text = asyncio.run(_fetch())
    except Exception as exc:
        logger.warning(f"scrape_page error ({url}): {exc}")
        text = ""

    _cache_set(key, text, ttl=3600)
    return text


def get_company_info(company_name: str) -> dict:
    """
    Search Exa for company info: industry, size, HQ, description.
    Returns a dict with whatever could be found.
    """
    key = _cache_key("company", company_name)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    results = search_web(
        f"{company_name} company overview headquarters industry funding",
        num_results=3,
    )
    info = {
        "company_name": company_name,
        "sources":      results,
        "summary":      results[0]["snippet"] if results else "",
    }
    _cache_set(key, info)
    return info


def get_artist_stats(artist_name: str) -> dict:
    """
    Search Exa for artist/performer info: genre, monthly listeners, tours.
    """
    key = _cache_key("artist", artist_name)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    results = search_web(
        f"{artist_name} artist Spotify monthly listeners genre tours 2025 2026",
        num_results=3,
    )
    info = {
        "artist_name": artist_name,
        "sources":     results,
        "summary":     results[0]["snippet"] if results else "",
    }
    _cache_set(key, info)
    return info


# ── tool dispatcher (used by agents in ReAct loop) ─────────────────────────────

AVAILABLE_TOOLS = {
    "search_web":       search_web,
    "scrape_page":      scrape_page,
    "get_company_info": get_company_info,
    "get_artist_stats": get_artist_stats,
}

def call_tool(tool_name: str, tool_args: dict) -> Any:
    """Dispatch a tool call from the LLM's function-calling response."""
    fn = AVAILABLE_TOOLS.get(tool_name)
    if not fn:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return fn(**tool_args)
    except Exception as exc:
        logger.warning(f"Tool {tool_name} failed: {exc}")
        return {"error": str(exc)}


# ── Groq function-calling schemas ─────────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search the web for current information using neural search. "
                "Use for finding recent news, sponsor budgets, artist tours, "
                "venue details, or any information not in the database. "
                "Use this instead of scraping — it returns snippets directly."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query — be specific for best results",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (1-5)",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_info",
            "description": (
                "Get company information: industry, headquarters, size, funding. "
                "Use for sponsor and exhibitor research."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company to research",
                    },
                },
                "required": ["company_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_artist_stats",
            "description": (
                "Get artist/performer stats: Spotify listeners, genre, upcoming tours. "
                "Use for speaker and artist agent research."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "artist_name": {
                        "type": "string",
                        "description": "Name of the artist or performer",
                    },
                },
                "required": ["artist_name"],
            },
        },
    },
]

"""Base scraper using Crawl4AI."""
import asyncio
import random
import logging
from abc import ABC, abstractmethod
from typing import Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

logger = logging.getLogger(__name__)

BROWSER_CONFIG = BrowserConfig(
    headless=True,
    viewport_width=1366,
    viewport_height=768,
    user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
)


class BaseScraper(ABC):
    """Base class for all Crawl4AI-based scrapers."""

    source_name: str = "unknown"
    rate_limit_min: float = 1.5  # seconds between requests
    rate_limit_max: float = 3.5
    max_concurrent: int = 3

    async def crawl_one(
        self, url: str, config: CrawlerRunConfig
    ) -> Any:
        async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
            result = await crawler.arun(url, config=config)
            if not result.success:
                logger.warning(f"[{self.source_name}] Failed: {url} — {result.error_message}")
            return result

    async def crawl_many(
        self, urls: list[str], config: CrawlerRunConfig
    ) -> list[Any]:
        results = []
        async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
            # Process in batches to respect rate limits
            for i in range(0, len(urls), self.max_concurrent):
                batch = urls[i : i + self.max_concurrent]
                batch_results = await crawler.arun_many(
                    urls=batch,
                    config=config,
                    max_concurrent=self.max_concurrent,
                )
                results.extend(batch_results)
                if i + self.max_concurrent < len(urls):
                    await asyncio.sleep(random.uniform(self.rate_limit_min, self.rate_limit_max))
        return results

    @abstractmethod
    async def scrape(self, **kwargs) -> list[dict]:
        """Scrape source and return raw event dicts."""

    @abstractmethod
    def normalize(self, raw: dict) -> dict | None:
        """Convert source-specific dict to unified event schema. Return None to skip."""

    async def run(self, **kwargs) -> list[dict]:
        """Full pipeline: scrape → normalize → filter Nones."""
        raw_events = await self.scrape(**kwargs)
        logger.info(f"[{self.source_name}] Scraped {len(raw_events)} raw records")
        normalized = [self.normalize(r) for r in raw_events]
        valid = [e for e in normalized if e is not None]
        logger.info(f"[{self.source_name}] {len(valid)} valid after normalization")
        return valid

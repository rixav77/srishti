from abc import ABC, abstractmethod
import asyncio
import logging
from time import time

from app.data.models import AgentOutput, EventConfig

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 8  # seconds — Groq TPM window needs real breathing room


class BaseAgent(ABC):
    """Base class for all Srishti agents."""

    name: str = "base_agent"
    description: str = ""

    def __init__(self, domain_config: dict | None = None):
        self.domain_config = domain_config or {}

    async def run(self, event_config: EventConfig, shared_state: dict) -> AgentOutput:
        start = time()
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                results = await self.execute(event_config, shared_state)
                elapsed = int((time() - start) * 1000)
                return AgentOutput(
                    agent_name=self.name,
                    status="completed",
                    results=results,
                    confidence_score=results.get("confidence", 0.7),
                    explanation=results.get("explanation", ""),
                    data_sources_used=results.get("data_sources", []),
                    execution_time_ms=elapsed,
                )
            except Exception as e:
                last_error = e
                err_msg = str(e)
                if "429" in err_msg or "rate_limit" in err_msg.lower():
                    backoff = RETRY_BACKOFF_BASE * (attempt + 1)
                    logger.warning(
                        f"[{self.name}] rate-limited, retry {attempt + 1}/{MAX_RETRIES} in {backoff}s"
                    )
                    await asyncio.sleep(backoff)
                    continue
                # Non-rate-limit error — don't retry
                break

        elapsed = int((time() - start) * 1000)
        return AgentOutput(
            agent_name=self.name,
            status="error",
            results={"error": str(last_error)},
            confidence_score=0,
            explanation=f"Agent failed after {MAX_RETRIES} attempts: {last_error}",
            execution_time_ms=elapsed,
        )

    @abstractmethod
    async def execute(self, event_config: EventConfig, shared_state: dict) -> dict:
        """Main agent logic. Override in subclass."""
        ...

    async def score_candidates(
        self, candidates: list[dict], weights: dict[str, float]
    ) -> list[dict]:
        """Score candidates using weighted multi-dimensional scoring."""
        scored = []
        for candidate in candidates:
            dimension_scores = {}
            total = 0.0
            for dimension, weight in weights.items():
                raw = candidate.get(f"score_{dimension}", 0.5)
                dimension_scores[dimension] = raw
                total += raw * weight
            scored.append(
                {
                    **candidate,
                    "total_score": round(total, 3),
                    "scores": dimension_scores,
                }
            )
        scored.sort(key=lambda x: x["total_score"], reverse=True)
        for i, item in enumerate(scored):
            item["rank"] = i + 1
        return scored

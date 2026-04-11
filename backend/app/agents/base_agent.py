from abc import ABC, abstractmethod
from time import time

from app.data.models import AgentOutput, EventConfig


class BaseAgent(ABC):
    """Base class for all Srishti agents."""

    name: str = "base_agent"
    description: str = ""

    def __init__(self, domain_config: dict | None = None):
        self.domain_config = domain_config or {}

    async def run(self, event_config: EventConfig, shared_state: dict) -> AgentOutput:
        start = time()
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
            elapsed = int((time() - start) * 1000)
            return AgentOutput(
                agent_name=self.name,
                status="error",
                results={"error": str(e)},
                confidence_score=0,
                explanation=f"Agent failed: {e}",
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

"""LangGraph orchestrator — runs all agents in wave-based parallel execution.

Wave 1 (parallel): SponsorAgent, SpeakerAgent, VenueAgent, ExhibitorAgent
Wave 2 (sequential, uses Wave 1 results): PricingAgent, GTMAgent, OpsAgent

Results are streamed via WebSocket as each agent completes.
Shared state is passed between waves so Wave 2 agents can use Wave 1 outputs.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator, Callable

from app.data.models import AgentOutput, EventConfig

logger = logging.getLogger(__name__)


# ── lazy imports to avoid circular deps ───────────────────────────────────────

def _load_wave1_agents():
    from app.agents.sponsor_agent   import SponsorAgent
    from app.agents.speaker_agent   import SpeakerAgent
    from app.agents.venue_agent     import VenueAgent
    from app.agents.exhibitor_agent import ExhibitorAgent
    return [SponsorAgent(), SpeakerAgent(), VenueAgent(), ExhibitorAgent()]


def _load_wave2_agents():
    from app.agents.pricing_agent import PricingAgent
    from app.agents.gtm_agent     import GTMAgent
    from app.agents.ops_agent     import OpsAgent
    return [PricingAgent(), OpsAgent(), GTMAgent()]


# ── orchestrator ──────────────────────────────────────────────────────────────

class Orchestrator:
    """
    Runs all 7 agents for a given EventConfig.

    Usage:
        orch = Orchestrator()
        async for update in orch.run_stream(config):
            # update = {"agent": "sponsor_agent", "status": "completed", "results": {...}}
            await websocket.send_json(update)

        final = await orch.run(config)   # returns ConsolidatedPlan dict
    """

    async def run(self, config: EventConfig) -> dict:
        """Run all waves, return consolidated results dict."""
        all_outputs: list[AgentOutput] = []
        shared_state: dict = {}

        # Wave 1 — staggered parallel (3s apart to avoid Groq TPM burst)
        wave1 = _load_wave1_agents()

        async def _run_staggered(agent, delay: float):
            if delay > 0:
                await asyncio.sleep(delay)
            return await agent.run(config, shared_state)

        wave1_tasks = [
            _run_staggered(agent, i * 3.0) for i, agent in enumerate(wave1)
        ]
        wave1_results = await asyncio.gather(*wave1_tasks, return_exceptions=True)

        for agent, result in zip(wave1, wave1_results):
            if isinstance(result, Exception):
                logger.error(f"[{agent.name}] failed: {result}")
                output = AgentOutput(
                    agent_name=agent.name,
                    status="error",
                    results={"error": str(result)},
                )
            else:
                output = result
            all_outputs.append(output)
            shared_state[agent.name] = output.results

        # Wave 2 — sequential (each can see previous wave's shared state)
        wave2 = _load_wave2_agents()
        for agent in wave2:
            try:
                output = await agent.run(config, shared_state)
            except Exception as exc:
                logger.error(f"[{agent.name}] failed: {exc}")
                output = AgentOutput(
                    agent_name=agent.name,
                    status="error",
                    results={"error": str(exc)},
                )
            all_outputs.append(output)
            shared_state[agent.name] = output.results

        return _consolidate(config, all_outputs, shared_state)

    async def run_stream(
        self, config: EventConfig
    ) -> AsyncGenerator[dict, None]:
        """
        Async generator — yields one update dict per agent as it completes.
        Wave 1 agents run in parallel; Wave 2 run sequentially after.
        """
        shared_state: dict = {}
        all_outputs:  list[AgentOutput] = []

        # ── Wave 1: staggered parallel (3s apart to respect Groq TPM) ────────
        wave1   = _load_wave1_agents()

        async def _delayed_run(agent, delay: float):
            if delay > 0:
                await asyncio.sleep(delay)
            return await agent.run(config, shared_state)

        pending = {
            asyncio.create_task(
                _delayed_run(agent, i * 3.0), name=agent.name
            ): agent
            for i, agent in enumerate(wave1)
        }

        while pending:
            done, _ = await asyncio.wait(pending.keys(), return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                agent = pending.pop(task)
                try:
                    output: AgentOutput = task.result()
                except Exception as exc:
                    output = AgentOutput(
                        agent_name=agent.name,
                        status="error",
                        results={"error": str(exc)},
                    )
                all_outputs.append(output)
                shared_state[agent.name] = output.results
                yield {
                    "wave":       1,
                    "agent":      output.agent_name,
                    "status":     output.status,
                    "results":    output.results,
                    "confidence": output.confidence_score,
                    "elapsed_ms": output.execution_time_ms,
                }

        # ── Wave 2: sequential ────────────────────────────────────────────────
        wave2 = _load_wave2_agents()
        for agent in wave2:
            yield {"wave": 2, "agent": agent.name, "status": "running", "results": {}}
            try:
                output = await agent.run(config, shared_state)
            except Exception as exc:
                output = AgentOutput(
                    agent_name=agent.name,
                    status="error",
                    results={"error": str(exc)},
                )
            all_outputs.append(output)
            shared_state[agent.name] = output.results
            yield {
                "wave":       2,
                "agent":      output.agent_name,
                "status":     output.status,
                "results":    output.results,
                "confidence": output.confidence_score,
                "elapsed_ms": output.execution_time_ms,
            }

        # Final consolidated plan
        plan = _consolidate(config, all_outputs, shared_state)
        yield {"wave": 0, "agent": "orchestrator", "status": "complete", "plan": plan}


# ── consolidation ─────────────────────────────────────────────────────────────

def _consolidate(
    config: EventConfig,
    outputs: list[AgentOutput],
    shared_state: dict,
) -> dict:
    """Merge all agent outputs into a single plan dict."""
    by_agent = {o.agent_name: o for o in outputs}

    return {
        "config": config.model_dump(),
        "status": "complete",
        "agents": {
            name: {
                "status":     o.status,
                "confidence": o.confidence_score,
                "elapsed_ms": o.execution_time_ms,
                "results":    o.results,
            }
            for name, o in by_agent.items()
        },
        # Convenience top-level fields for the frontend
        "sponsors":   shared_state.get("sponsor_agent",   {}).get("sponsors",   []),
        "speakers":   shared_state.get("speaker_agent",   {}).get("talents",    []),
        "venues":     shared_state.get("venue_agent",     {}).get("venues",     []),
        "exhibitors": shared_state.get("exhibitor_agent", {}).get("exhibitors", []),
        "pricing":    shared_state.get("pricing_agent",   {}),
        "gtm":        shared_state.get("gtm_agent",       {}),
        "ops":        shared_state.get("ops_agent",       {}),
    }

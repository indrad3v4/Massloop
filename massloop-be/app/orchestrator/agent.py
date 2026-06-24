"""OpenAI Agents SDK orchestrator for Massloop music generation."""

import os
from typing import Optional

from openai import AsyncOpenAI
from agents import Agent, Runner, function_tool, set_default_openai_client
from agents.tracing import set_tracing_disabled
from loguru import logger


# Disable OpenAI platform tracing; we route through CometAPI.
set_tracing_disabled(True)

from app.config import settings
from .prompts import MUSIC_ORCHESTRATOR_SYSTEM_PROMPT, build_orchestrator_context
from .tools import generate_track, poll_track, get_style_suggestions


# Route the OpenAI Agents SDK through CometAPI's OpenAI-compatible endpoint.
if settings.cometapi_key:
    client = AsyncOpenAI(
        api_key=settings.cometapi_key,
        base_url="https://api.cometapi.com/v1",
    )
    set_default_openai_client(client)
    os.environ.setdefault("COMETAPI_KEY", settings.cometapi_key)


@function_tool
def tool_generate_track(
    prompt: str,
    tags: str,
    title: str = "Massloop Track",
    mv: str = "chirp-v4",
    make_instrumental: bool = True,
) -> dict:
    """Submit a track generation request to CometAPI Suno."""
    return generate_track(prompt=prompt, tags=tags, title=title, mv=mv, make_instrumental=make_instrumental)


@function_tool
def tool_poll_track(task_id: str, max_wait_s: int = 120) -> dict:
    """Poll CometAPI until the track is ready."""
    return poll_track(task_id=task_id, max_wait_s=max_wait_s)


@function_tool
def tool_get_style_suggestions(bpm: int, energy: float, venue: str) -> str:
    """Get style tag suggestions for the performance context."""
    return get_style_suggestions(bpm=bpm, energy=energy, venue=venue)


class MusicOrchestratorAgent:
    """
    Agentic orchestrator that decides when and what to generate,
    then calls CometAPI Suno tools to produce tracks.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.agent = Agent(
            name="massloop_music_orchestrator",
            instructions=MUSIC_ORCHESTRATOR_SYSTEM_PROMPT,
            model=model,
            tools=[
                tool_generate_track,
                tool_poll_track,
                tool_get_style_suggestions,
            ],
        )
        logger.info(f"MusicOrchestratorAgent initialized with model {model}")

    async def decide_and_generate(
        self,
        bpm: int,
        energy: float,
        venue: str,
        style: str,
        theme: str = "",
        crowd_energy: float = 0.5,
        artist_brand: dict | None = None,
    ) -> dict:
        """
        Run the orchestrator to decide and generate a track.

        Returns:
            dict with decision, task_id, audio_url (if ready), and metadata.
        """
        context = build_orchestrator_context(
            bpm=bpm,
            energy=energy,
            venue=venue,
            style=style,
            theme=theme,
            crowd_energy=crowd_energy,
            artist_brand=artist_brand,
        )

        prompt = (
            f"{context}\n\n"
            "Decide the next action and execute it. "
            "If you decide to generate, call get_style_suggestions first, "
            "then generate_track, then poll_track until you have the audio_url. "
            "Return the final audio_url and all parameters used."
        )

        try:
            result = await Runner.run(self.agent, input=prompt)
            output = result.final_output

            # Try to extract audio_url from the agent's final text
            audio_url = None
            task_id = None
            for line in output.splitlines():
                lower = line.lower()
                if "audio_url" in lower or "audio url" in lower:
                    audio_url = line.split(":", 1)[-1].strip()
                if "task_id" in lower or "task id" in lower:
                    task_id = line.split(":", 1)[-1].strip()

            return {
                "decision": "generate",
                "agent_output": output,
                "audio_url": audio_url,
                "task_id": task_id,
                "context": context,
            }
        except Exception as e:
            logger.error(f"Orchestrator run failed: {e}")
            return {"error": str(e), "context": context}

    async def optimize_generation_request(
        self,
        base_request: object,
        crowd_energy: float,
        performance_state: object,
        artist_profile: object,
        max_reflection_iterations: int = 1,
    ) -> tuple:
        """
        Compatibility shim for LivePerformanceUseCase.
        Returns the base request unchanged and empty metadata.
        """
        logger.debug("Orchestrator optimize_generation_request shim called")
        return base_request, {}

    async def evaluate_track_quality(self, track: object, expected_request: object) -> dict:
        """
        Compatibility shim for LivePerformanceUseCase quality evaluation.
        Returns a neutral quality score.
        """
        logger.debug("Orchestrator evaluate_track_quality shim called")
        return {"overall_score": 0.75}

    async def analyze_cost_efficiency(self, state: object) -> object:
        """
        Compatibility shim for LivePerformanceUseCase cost analysis.
        Returns a simple ROI object.
        """
        from types import SimpleNamespace

        logger.debug("Orchestrator analyze_cost_efficiency shim called")
        return SimpleNamespace(total_cost_eur=0.0, avg_quality_score=0.75)

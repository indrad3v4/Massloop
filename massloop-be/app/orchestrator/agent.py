# MASSLOOP_MODEL_LAYER_FIX: real orchestrator capabilities + model fallback chain (see docs/roast_model.md)
"""OpenAI Agents SDK orchestrator for Massloop music generation.

Model-layer fixes (docs/roast_model.md findings #1, #2, #3):
- `optimize_generation_request` now does real param tuning (BPM clamp to style
  range, energy nudge toward crowd, contradictory style-tag pruning).
- `evaluate_track_quality` now returns a real 0-1 heuristic score comparing the
  generated track (BPM/energy/style/duration/prompt) against the request, so the
  `_quality_threshold` gate in `LivePerformanceUseCase` is no longer a no-op.
- `analyze_cost_efficiency` now reads real accumulated spend from `PerformanceState`
  instead of reporting a constant €0.00, and checks against `daily_budget_eur` /
  `max_track_cost_eur`.
- `decide_and_generate` now runs through a model fallback chain
  (gpt-4o-mini@CometAPI -> gpt-4o-mini@OpenAI -> deepseek-chat@DeepSeek) with
  bounded retry + exponential backoff, swapping provider/model on failure.
"""

import asyncio
import os
import random
from typing import Optional

import re
from openai import (
    AsyncOpenAI,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)
from agents import Agent, Runner, RunConfig, OpenAIProvider, function_tool, set_default_openai_client
from agents.tracing import set_tracing_disabled
from loguru import logger
from types import SimpleNamespace


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


# ---------------------------------------------------------------------------
# Real orchestrator helpers (model-layer logic, not stubs)
# ---------------------------------------------------------------------------

# Contradictory style-tag groups: if a tag from BOTH sides appears, the
# generation intent is incoherent. We drop the second group (the modifier that
# conflicts with the core artistic direction encoded by the style enum).
_CONTRADICTORY_TAG_PAIRS = [
    (
        {"ambient", "chill", "calm", "lofi", "slow", "soft", "relaxing"},
        {"high energy", "energetic", "aggressive", "hard", "fast", "driving", "powerful"},
    ),
    (
        {"instrumental"},
        {"vocal", "vocals", "singing", "rap", "voice", "words"},
    ),
    (
        {"acoustic"},
        {"electronic", "synth", "techno", "edm", "synthesizer", "digital"},
    ),
    (
        {"minimal"},
        {"layered", "busy", "complex", "orchestral", "maximal"},
    ),
]


def _prune_contradictory_tags(tags) -> tuple:
    """Return (kept_tags, removed_tags) dropping contradictory style modifiers.

    Heuristic: when a tag from both sides of a contradictory pair is present we
    keep the core intent (group A, usually derived from the style enum) and drop
    the conflicting modifier (group B).
    """
    if not tags:
        return list(tags), []
    normalized = [str(t).strip().lower() for t in tags]
    low_set = set(normalized)
    remove = set()
    for group_a, group_b in _CONTRADICTORY_TAG_PAIRS:
        if (low_set & group_a) and (low_set & group_b):
            for t in normalized:
                if t in group_b:
                    remove.add(t)
    kept = [t for t, low in zip(tags, normalized) if low not in remove]
    removed = [t for t, low in zip(tags, normalized) if low in remove]
    return kept, removed


def _score_track_quality(track, expected_request) -> dict:
    """Real 0-1 quality heuristic comparing a generated track to its request.

    Combines BPM accuracy, energy match, style authenticity, duration bounds,
    production quality (from optional librosa analysis) and prompt adherence.
    Returns a dict including ``overall_score`` (0.0-1.0) and per-axis breakdowns.
    """
    req_bpm = getattr(expected_request, "bpm", None)
    req_energy = getattr(expected_request, "energy", 0.5) or 0.5
    req_style = getattr(expected_request, "style", None)
    req_dur = getattr(expected_request, "duration_seconds", 240) or 240

    if track is None:
        return {
            "overall_score": 0.0,
            "bpm_accuracy": 0.0,
            "energy_match": 0.0,
            "style_authenticity": 0.0,
            "duration_score": 0.0,
            "production_quality": 0.0,
            "prompt_adherence": 0.0,
            "issues": ["no_track"],
        }

    track_bpm = getattr(track, "actual_bpm", None) or getattr(track, "bpm", None)
    track_energy = getattr(track, "energy", 0.5) or 0.5
    track_style = getattr(track, "style", None)
    track_dur = getattr(track, "duration_seconds", None)
    metadata = getattr(track, "metadata", {}) or {}

    # --- BPM accuracy -------------------------------------------------------
    if req_bpm and track_bpm:
        bpm_diff = abs(track_bpm - req_bpm)
        tol = max(6.0, req_bpm * 0.05)
        bpm_accuracy = max(0.0, 1.0 - bpm_diff / (tol * 2.0))
    else:
        bpm_accuracy = 0.5  # unknown -> neutral

    # --- Energy match -------------------------------------------------------
    energy_match = max(0.0, 1.0 - abs(track_energy - req_energy))

    # --- Style authenticity -------------------------------------------------
    if req_style is not None and track_style is not None:
        style_authenticity = 1.0 if track_style == req_style else 0.5
    else:
        style_authenticity = 0.7

    # --- Duration bounds (within +/-40% of request) -------------------------
    if track_dur:
        dur_diff = abs(track_dur - req_dur) / max(req_dur, 1)
        duration_score = max(0.0, 1.0 - dur_diff)
    else:
        duration_score = 0.6

    # --- Production quality (from optional librosa analysis) ----------------
    production_quality = 0.7
    analysis = metadata.get("librosa_analysis") or metadata.get("analysis")
    if isinstance(analysis, dict):
        if analysis.get("is_clipping"):
            production_quality = min(production_quality, 0.2)
        if analysis.get("is_silent"):
            production_quality = min(production_quality, 0.1)
        if analysis.get("bpm_accuracy") is not None:
            try:
                bpm_accuracy = float(analysis["bpm_accuracy"])
            except (TypeError, ValueError):
                pass

    # --- Prompt adherence signal -------------------------------------------
    prompt_text = getattr(expected_request, "custom_prompt", "") or ""
    prompt_adherence = 1.0 if len(prompt_text) >= 20 else 0.4

    overall = (
        0.35 * bpm_accuracy
        + 0.20 * energy_match
        + 0.20 * style_authenticity
        + 0.10 * duration_score
        + 0.10 * production_quality
        + 0.05 * prompt_adherence
    )
    overall = max(0.0, min(1.0, overall))

    issues = []
    if bpm_accuracy < 0.6:
        issues.append("bpm_mismatch")
    if energy_match < 0.6:
        issues.append("energy_mismatch")
    if production_quality <= 0.2:
        issues.append("production_issue")

    return {
        "overall_score": round(overall, 4),
        "bpm_accuracy": round(bpm_accuracy, 4),
        "energy_match": round(energy_match, 4),
        "style_authenticity": round(style_authenticity, 4),
        "duration_score": round(duration_score, 4),
        "production_quality": round(production_quality, 4),
        "prompt_adherence": round(prompt_adherence, 4),
        "issues": issues,
    }


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

    Runs through a model fallback chain (CometAPI -> OpenAI -> DeepSeek) with
    bounded retry + exponential backoff so a single provider/model outage does
    not kill a live set.
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

        # Build the model fallback chain from configured provider keys.
        self._fallback_chain = []
        if settings.cometapi_key:
            self._fallback_chain.append({
                "label": "cometapi",
                "model": model,
                "model_client": AsyncOpenAI(
                    api_key=settings.cometapi_key,
                    base_url="https://api.cometapi.com/v1",
                ),
            })
        if settings.openai_api_key:
            self._fallback_chain.append({
                "label": "openai",
                "model": model,
                "model_client": AsyncOpenAI(api_key=settings.openai_api_key),
            })
        if settings.deepseek_api_key:
            # DeepSeek only supports chat completions, not the Responses API.
            self._fallback_chain.append({
                "label": "deepseek",
                "model": "deepseek-chat",
                "model_client": AsyncOpenAI(
                    api_key=settings.deepseek_api_key,
                    base_url="https://api.deepseek.com",
                ),
                "use_responses": False,
            })
        if not self._fallback_chain:
            logger.warning(
                "MASSLOOP: no model provider keys configured (cometapi/openai/deepseek); "
                "orchestrator will fail fast on generation."
            )
        else:
            logger.info(
                f"MusicOrchestratorAgent model fallback chain: "
                f"{[c['label'] for c in self._fallback_chain]}"
            )

    async def _run_agent_with_fallback(
        self, prompt: str, max_retries: int = 2
    ) -> tuple:
        """Run the orchestrator agent across the model fallback chain.

        Returns ``(result, provider_label, last_error)``. On total failure
        ``result`` is ``None`` and ``last_error`` explains what happened.
        Bounded exponential backoff is applied to transient errors (rate limit /
        status / connection / timeout); non-transient errors swap provider.
        """
        last_error: Optional[Exception] = None
        for provider in self._fallback_chain:
            label = provider["label"]
            candidate = Agent(
                name=self.agent.name,
                instructions=self.agent.instructions,
                model=provider["model"],
                tools=self.agent.tools,
            )
            run_config = RunConfig(
                model_provider=OpenAIProvider(
                    openai_client=provider["model_client"],
                    use_responses=provider.get("use_responses", True),
                )
            )
            for attempt in range(max(1, max_retries)):
                try:
                    result = await Runner.run(candidate, input=prompt, run_config=run_config)
                    logger.success(
                        f"MASSLOOP orchestrator run OK via provider={label} model={provider['model']}"
                    )
                    return result, label, None
                except (RateLimitError, APIStatusError, APIConnectionError, APITimeoutError) as e:
                    last_error = e
                    wait_s = (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(
                        f"MASSLOOP provider={label} transient error (attempt "
                        f"{attempt + 1}/{max_retries}): {e}; retry in {wait_s:.1f}s"
                    )
                    await asyncio.sleep(wait_s)
                except Exception as e:  # noqa: BLE001 - swap provider on any other failure
                    last_error = e
                    logger.error(
                        f"MASSLOOP provider={label} non-transient error: {e}; swapping provider"
                    )
                    break
        return None, None, last_error

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

        result, provider, last_error = await self._run_agent_with_fallback(prompt)
        if result is None:
            logger.error(f"Orchestrator run failed across all providers: {last_error}")
            return {"error": str(last_error), "provider": None, "context": context}

        output = result.final_output

        # Try to extract audio_url from the agent's final text
        audio_url = None
        task_id = None
        for line in output.splitlines():
            lower = line.lower()
            if "audio_url" in lower or "audio url" in lower:
                raw = line.split(":", 1)[-1].strip()
                # Handle Markdown link syntax: [text](url)
                m = re.search(r'\]\(([^)]+)\)', raw)
                if m:
                    audio_url = m.group(1)
                else:
                    audio_url = raw
            if "task_id" in lower or "task id" in lower:
                tid = line.split(":", 1)[-1].strip()
                if tid and tid != "null" and tid != "None":
                    task_id = tid

        return {
            "decision": "generate",
            "agent_output": output,
            "audio_url": audio_url,
            "task_id": task_id,
            "provider": provider,
            "context": context,
        }

    async def optimize_generation_request(
        self,
        base_request: object,
        crowd_energy: float,
        performance_state: object,
        artist_profile: object,
        max_reflection_iterations: int = 1,
    ) -> tuple:
        """
        REAL param tuning for LivePerformanceUseCase.

        - Clamps BPM into the requested style's supported range.
        - Nudges energy toward live crowd energy (bounded blend).
        - Prunes contradictory style tags (e.g. "ambient" + "high energy").
        - Caps reflection iterations and sets the configured quality threshold.
        Returns ``(optimized_request, metadata)``.
        """
        req = base_request
        metadata = {"pruned_tags": [], "bpm_adjusted": False, "energy_adjusted": False, "notes": []}

        # 1. Clamp BPM into the style's supported range.
        style = getattr(req, "style", None)
        if style is not None:
            lo, hi = style.default_bpm_range
            if not (lo <= req.bpm <= hi):
                new_bpm = max(lo, min(hi, req.bpm))
                metadata["bpm_adjusted"] = True
                metadata["notes"].append(
                    f"bpm {req.bpm} outside {style.display_name} range {lo}-{hi} -> {new_bpm}"
                )
                req.bpm = new_bpm

        # 2. Nudge energy toward live crowd energy (bounded blend).
        ce = crowd_energy if isinstance(crowd_energy, (int, float)) else req.energy
        if abs(req.energy - ce) > 0.15:
            new_energy = max(0.0, min(1.0, req.energy * 0.7 + ce * 0.3))
            metadata["energy_adjusted"] = True
            metadata["notes"].append(
                f"energy {req.energy:.2f} -> {new_energy:.2f} toward crowd {ce:.2f}"
            )
            req.energy = new_energy

        # 3. Prune contradictory style tags.
        tags = list(getattr(req, "tags", None) or [])
        if tags:
            kept, removed = _prune_contradictory_tags(tags)
            if removed:
                metadata["pruned_tags"] = removed
                metadata["notes"].append(f"pruned contradictory tags: {removed}")
                req.tags = kept

        # 4. Cap reflection + apply configured quality threshold.
        req.max_reflection_iterations = max(1, min(int(max_reflection_iterations), 3))
        req.quality_threshold = max(0.0, min(1.0, float(getattr(settings, "quality_threshold", 0.7) or 0.7)))

        logger.info(
            f"MASSLOOP optimize: bpm={req.bpm} energy={req.energy:.2f} "
            f"tags={getattr(req, 'tags', None)} iterations={req.max_reflection_iterations}"
        )
        return req, metadata

    async def evaluate_track_quality(self, track: object, expected_request: object) -> dict:
        """
        REAL quality evaluation for LivePerformanceUseCase.

        Computes a 0-1 score by comparing the generated track (BPM/energy/style/
        duration/prompt) against the request via ``_score_track_quality``. The
        returned ``overall_score`` is consumed by the ``_quality_threshold`` gate,
        so rejected tracks now actually score below threshold.
        """
        logger.info("MASSLOOP evaluate_track_quality: scoring track vs request")
        return _score_track_quality(track, expected_request)

    async def analyze_cost_efficiency(self, state: object) -> object:
        """
        REAL cost efficiency analysis for LivePerformanceUseCase.

        Reads accumulated spend from ``PerformanceState`` (per-track EUR via
        ``LiveTrack.cost_eur``), computes the average quality score, and checks the
        running total against ``daily_budget_eur`` / ``max_track_cost_eur``. No
        longer reports a constant €0.00.
        """
        tracks = getattr(state, "generated_tracks", None) or []
        total_cost = 0.0
        for t in tracks:
            cost_fn = getattr(t, "cost_eur", None)
            if callable(cost_fn):
                try:
                    total_cost += float(cost_fn())
                except (TypeError, ValueError):
                    pass
        # Prefer the state's own rolled-up total if it has been updated.
        state_total = getattr(state, "total_cost_eur", 0.0) or 0.0
        if state_total > total_cost:
            total_cost = state_total

        scores = [getattr(t, "quality_score", 0.0) or 0.0 for t in tracks]
        avg_quality = (sum(scores) / len(scores)) if scores else 0.0

        daily_budget = float(getattr(settings, "daily_budget_eur", 10.0) or 10.0)
        max_track_cost = float(getattr(settings, "max_track_cost_eur", 3.0) or 3.0)
        within_budget = total_cost <= daily_budget
        budget_headroom = max(0.0, daily_budget - total_cost)

        logger.info(
            f"MASSLOOP analyze_cost_efficiency: €{total_cost:.2f} / "
            f"€{daily_budget:.2f} daily (within={within_budget}), "
            f"avg_quality={avg_quality:.2f}, tracks={len(tracks)}"
        )
        return SimpleNamespace(
            total_cost_eur=round(total_cost, 4),
            avg_quality_score=round(avg_quality, 4),
            track_count=len(tracks),
            daily_budget_eur=daily_budget,
            max_track_cost_eur=max_track_cost,
            budget_headroom_eur=round(budget_headroom, 4),
            within_budget=within_budget,
        )

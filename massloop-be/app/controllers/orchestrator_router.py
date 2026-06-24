"""Orchestrator chat router — real LLM agent via MusicOrchestratorAgent."""
import asyncio
import random
from typing import Optional

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from app.orchestrator import MusicOrchestratorAgent

router = APIRouter(prefix="/api/chat", tags=["orchestrator"])

# Lazy-init — will be wired in main.py
_orchestrator: MusicOrchestratorAgent | None = None


def set_orchestrator(orch: MusicOrchestratorAgent):
    """Inject the orchestrator instance from main.py."""
    global _orchestrator
    _orchestrator = orch


class ChatRequest(BaseModel):
    message: str = ""
    context: dict = {}


class ChatResponse(BaseModel):
    reply: str = ""
    action: str | None = None
    auto_generate: bool = False


# ── Fallback suggestions (used when orchestrator is unavailable) ──
_SUGGESTIONS = [
    "push the crowd harder — +5 BPM incoming",
    "time to strip it back, let the bass breathe",
    "layer a perc loop under the kick, keep it rolling",
    "tease the drop — filter sweep then full release",
    "switch to minor key, darken the mood",
    "double the snare, build tension for 16 bars",
]


def _fallback_chat(msg: str, context: dict) -> ChatResponse:
    """Rule-based fallback when the LLM orchestrator is not available."""
    msg_lower = msg.lower().strip()
    bpm = context.get("bpm", 140)
    energy = context.get("energy", 0.7)

    if "energy" in msg_lower or "bpm" in msg_lower or "tempo" in msg_lower:
        if "energy" in msg_lower:
            return ChatResponse(
                reply=f"energy's at {energy} — let's push it +0.1, the floor needs it 🔥",
                action="bump_energy",
            )
        return ChatResponse(
            reply=f"sitting at {bpm} BPM — bumping +5 to keep the drive alive",
            action="bump_bpm",
        )
    if "drop" in msg_lower:
        return ChatResponse(
            reply="DROP incoming — 16-bar build, filter open, full release on the 1 💥",
        )
    if "build" in msg_lower:
        return ChatResponse(
            reply="build mode: strip hats, ride the riser, snare roll at bar 14 → drop",
        )
    if "break" in msg_lower or "breakdown" in msg_lower:
        return ChatResponse(
            reply="breakdown time — mute the kick, let the pad breathe, 32 bars then re-enter",
        )
    if "style" in msg_lower or "genre" in msg_lower:
        return ChatResponse(
            reply="switching to ACID_TECHNO — 303 squelch, hardgroove percussion, industrial edge",
        )
    if "acid" in msg_lower:
        return ChatResponse(
            reply="ACID mode engaged — TB-303 resonance up, cutoff sweeping, 140 BPM locked",
        )
    if "industrial" in msg_lower:
        return ChatResponse(
            reply="INDUSTRIAL shift — distorted kicks, metallic hats, dystopian atmosphere",
        )
    if "hardgroove" in msg_lower:
        return ChatResponse(
            reply="HARDGROOVE — syncopated percussion, rolling bass, 135 BPM sweet spot",
        )
    return ChatResponse(
        reply=f"got it — {random.choice(_SUGGESTIONS)}",
    )


@router.post("/orchestrator", response_model=ChatResponse)
async def orchestrator_chat(req: ChatRequest):
    """LLM-powered orchestrator chat — uses MusicOrchestratorAgent when available."""
    msg = req.message.lower().strip()
    context = req.context or {}

    # If orchestrator is not initialized, fall back to rule-based
    if _orchestrator is None:
        logger.info("Orchestrator agent unavailable — using rule-based fallback")
        return _fallback_chat(msg, context)

    # Extract parameters from context with sensible defaults
    bpm = context.get("bpm", 140)
    energy = context.get("energy", 0.7)
    venue = context.get("venue", "club")
    style = context.get("style", "acid_techno")
    theme = context.get("theme", "")
    crowd_energy = context.get("crowd_energy", 0.5)

    logger.info(f"Orchestrator chat: bpm={bpm}, energy={energy}, venue={venue}, style={style}")

    try:
        # Run the agent with a 55-second timeout (leaving 5s for response formatting)
        result = await asyncio.wait_for(
            _orchestrator.decide_and_generate(
                bpm=bpm,
                energy=energy,
                venue=venue,
                style=style,
                theme=theme,
                crowd_energy=crowd_energy,
            ),
            timeout=55,
        )

        if "error" in result:
            logger.error(f"Orchestrator error: {result['error']}")
            return ChatResponse(
                reply=f"🤖 orchestrator hit a snag: {result['error'][:100]}",
                auto_generate=False,
            )

        # Extract the agent's reasoning text as the reply
        agent_output = result.get("agent_output", "")
        audio_url = result.get("audio_url")

        # Build a concise reply from the agent's reasoning
        # Take the first few lines as the chat response
        reply_lines = []
        for line in agent_output.splitlines():
            line = line.strip()
            if line and not line.startswith("audio_url") and not line.startswith("task_id"):
                reply_lines.append(line)
            if len(reply_lines) >= 6:
                break

        reply = "\n".join(reply_lines) if reply_lines else agent_output[:300]

        # Determine if the agent decided to generate
        auto_generate = audio_url is not None

        logger.info(f"Orchestrator reply (auto_generate={auto_generate}): {reply[:80]}...")

        return ChatResponse(
            reply=reply[:500],
            auto_generate=auto_generate,
        )

    except asyncio.TimeoutError:
        logger.warning("Orchestrator chat timed out after 55s")
        return ChatResponse(
            reply="⏳ taking longer than expected — the agents are working on it. Try again in a moment.",
            auto_generate=False,
        )
    except Exception as e:
        logger.error(f"Orchestrator chat exception: {e}")
        return ChatResponse(
            reply=f"🤖 orchestrator encountered an issue: {str(e)[:100]}",
            auto_generate=False,
        )

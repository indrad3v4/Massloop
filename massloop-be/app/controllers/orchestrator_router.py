"""Orchestrator chat router — rule-based music creative-strategist persona."""
import random
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["orchestrator"])


class ChatRequest(BaseModel):
    message: str = ""
    context: dict = {}


class ChatResponse(BaseModel):
    reply: str = ""
    action: str | None = None


_SUGGESTIONS = [
    "push the crowd harder — +5 BPM incoming",
    "time to strip it back, let the bass breathe",
    "layer a perc loop under the kick, keep it rolling",
    "tease the drop — filter sweep then full release",
    "switch to minor key, darken the mood",
    "double the snare, build tension for 16 bars",
]


@router.post("/orchestrator", response_model=ChatResponse)
async def orchestrator_chat(req: ChatRequest):
    """Rule-based orchestrator chat — no external LLM required for v1."""
    msg = req.message.lower().strip()
    bpm = req.context.get("bpm", 140)
    energy = req.context.get("energy", 0.7)

    # ── Energy / BPM ──
    if "energy" in msg or "bpm" in msg or "tempo" in msg:
        if "energy" in msg:
            return ChatResponse(
                reply=f"energy's at {energy} — let's push it +0.1, the floor needs it 🔥",
                action="bump_energy",
            )
        return ChatResponse(
            reply=f"sitting at {bpm} BPM — bumping +5 to keep the drive alive",
            action="bump_bpm",
        )

    # ── Arrangement ──
    if "drop" in msg:
        return ChatResponse(
            reply="DROP incoming — 16-bar build, filter open, full release on the 1 💥",
            action=None,
        )
    if "build" in msg:
        return ChatResponse(
            reply="build mode: strip hats, ride the riser, snare roll at bar 14 → drop",
            action=None,
        )
    if "break" in msg or "breakdown" in msg:
        return ChatResponse(
            reply="breakdown time — mute the kick, let the pad breathe, 32 bars then re-enter",
            action=None,
        )

    # ── Style / Genre ──
    if "style" in msg or "genre" in msg:
        return ChatResponse(
            reply="switching to ACID_TECHNO — 303 squelch, hardgroove percussion, industrial edge",
            action=None,
        )
    if "acid" in msg:
        return ChatResponse(
            reply="ACID mode engaged — TB-303 resonance up, cutoff sweeping, 140 BPM locked",
            action=None,
        )
    if "industrial" in msg:
        return ChatResponse(
            reply="INDUSTRIAL shift — distorted kicks, metallic hats, dystopian atmosphere",
            action=None,
        )
    if "hardgroove" in msg:
        return ChatResponse(
            reply="HARDGROOVE — syncopated percussion, rolling bass, 135 BPM sweet spot",
            action=None,
        )

    # ── Default ──
    return ChatResponse(
        reply=f"got it — {random.choice(_SUGGESTIONS)}",
        action=None,
    )
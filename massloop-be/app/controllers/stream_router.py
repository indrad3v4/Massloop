"""SSE streaming orchestrator — streams agent reasoning token by token."""
import asyncio
import json
import uuid
import random
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from app.orchestrator import MusicOrchestratorAgent
from ..services.artist_memory import learn_from_chat, build_artist_context

router = APIRouter(prefix="/api/chat", tags=["orchestrator-stream"])

_orchestrator: MusicOrchestratorAgent | None = None

def set_orchestrator(orch: MusicOrchestratorAgent):
    global _orchestrator
    _orchestrator = orch


class StreamRequest(BaseModel):
    message: str = ""
    context: dict = {}
    artist_brand: dict = {}
    artist_id: str = ""


async def _sse_reasoning_stream(
    message: str,
    context: dict,
    artist_brand: dict,
) -> AsyncGenerator[str, None]:
    """Stream agent reasoning as SSE events."""
    artist_id = artist_brand.get("artist_id") or context.get("artist_id", "")

    # 1. Send the user's message immediately
    yield f"data: {json.dumps({'type': 'user', 'text': message})}\n\n"

    if _orchestrator is None:
        # Fallback: send a quick thought
        yield f"data: {json.dumps({'type': 'reasoning', 'text': '🤖 processing your request...'})}\n\n"
        await asyncio.sleep(0.3)
        
        # Simulate reasoning steps
        steps = [
            "analyzing your prompt...",
            "checking style parameters...",
            "preparing track structure...",
        ]
        for step in steps:
            await asyncio.sleep(0.5)
            yield f"data: {json.dumps({'type': 'reasoning', 'text': step})}\n\n"
        
        # Return a default response
        default_replies = [
            "got it — push the crowd harder, +5 BPM incoming 🔥",
            "time to strip it back, let the bass breathe",
            "layer a perc loop under the kick, keep it rolling",
            "switching to ACID_TECHNO — 303 squelch, hardgroove percussion"
        ]
        reply = random.choice(default_replies)
        yield f"data: {json.dumps({'type': 'reply', 'text': reply, 'auto_generate': False})}\n\n"
        return

    # 2. Learn from chat
    if artist_id:
        learn_from_chat(artist_id, message)
        artist_ctx = build_artist_context(artist_id)
        if artist_ctx:
            yield f"data: {json.dumps({'type': 'reasoning', 'text': f'🎯 artist profile loaded: {artist_ctx[:100]}...'})}\n\n"
            await asyncio.sleep(0.3)

    # 3. Stream agent reasoning
    bpm = context.get("bpm", 140)
    energy = context.get("energy", 0.7)
    venue = context.get("venue", "club")
    style = context.get("style", "acid_techno")
    theme = context.get("theme", "")

    yield f"data: {json.dumps({'type': 'reasoning', 'text': '🧠 calling the orchestrator agent...'})}\n\n"

    try:
        # Run with streamed output
        result = await asyncio.wait_for(
            _orchestrator.decide_and_generate(
                bpm=bpm, energy=energy, venue=venue,
                style=style, theme=theme, crowd_energy=context.get("crowd_energy", 0.5),
                artist_brand=artist_brand or None,
            ),
            timeout=55,
        )

        agent_output = result.get("agent_output", "")
        audio_url = result.get("audio_url")

        # Stream the reasoning line by line
        for line in agent_output.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("audio_url") or line.startswith("task_id"):
                continue
            await asyncio.sleep(0.3)  # simulate token-by-token delivery
            yield f"data: {json.dumps({'type': 'reasoning', 'text': line})}\n\n"

        # Stream the reply
        reply_lines = [l for l in agent_output.splitlines() if l.strip() and not l.startswith("audio_url") and not l.startswith("task_id")]
        reply = "\n".join(reply_lines[:6]) if reply_lines else agent_output[:300]

        yield f"data: {json.dumps({'type': 'reply', 'text': reply[:500], 'auto_generate': audio_url is not None})}\n\n"

        # If audio generated, send the URL
        if audio_url:
            yield f"data: {json.dumps({'type': 'audio', 'url': audio_url, 'task_id': result.get('task_id', '')})}\n\n"

    except asyncio.TimeoutError:
        yield f"data: {json.dumps({'type': 'error', 'text': '⏳ orchestration timed out — try again'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'text': f'🤖 error: {str(e)[:80]}'})}\n\n"

    yield "data: [DONE]\n\n"


@router.post("/stream")
async def chat_stream(req: StreamRequest):
    """SSE streaming endpoint for orchestrator reasoning."""
    return StreamingResponse(
        _sse_reasoning_stream(
            message=req.message,
            context=req.context or {},
            artist_brand=req.artist_brand or {},
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

"""Performance router - Live performance endpoints wired to business logic"""
import asyncio
import json
import time
import uuid
import os
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from app.controllers.usecases import (
    LivePerformanceUseCase, SetupProfileUseCase, DeckStateManager
)
from app.models.entities import ArtistProfile, UndergroundStyle, VenueType

router = APIRouter(prefix="/api/performance", tags=["performance"])

# Lazy init — will be wired in main.py
use_case: LivePerformanceUseCase = None
_orchestrator = None


def set_orchestrator(orch):
    """Inject the orchestrator instance from main.py."""
    global _orchestrator
    _orchestrator = orch

# Production-safe: resolves relative to the repo root or uses env var
_DATA_DIR = Path(__file__).parent.parent.parent / "data"
QUEUE_FILE = Path(os.getenv("MASSLOOP_DATA_DIR", str(_DATA_DIR))) / "queue.json"


class QueueRequest(BaseModel):
    prompt: str = "test"
    style: str = "ACID_TECHNO"
    bpm: int = 124
    energy: float = 0.7
    venue: str = "club"
    theme: str = ""


class ApproveRequest(BaseModel):
    approved_by: str = "operator"


def _load_queue() -> list:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not QUEUE_FILE.exists():
        return []
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_queue(queue: list):
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, default=str)


def _find_task(queue: list, task_id: str) -> Optional[dict]:
    for task in queue:
        if task.get("id") == task_id:
            return task
    return None


@router.post("/start")
async def start_performance(
    event: str = "Live Set",
    profile_name: str = "default",
    style: str = "raw_techno",
    venue: str = "club",
    duration: int = 60,
    theme: str = ""
):
    """Start a live performance with the given artist profile"""
    global use_case
    if not use_case:
        raise HTTPException(503, "Performance service not initialized")

    try:
        # Map enum values
        style_enum = UndergroundStyle(style)
        venue_enum = VenueType(venue)
        profile = ArtistProfile(
            name=profile_name,
            styles=[style_enum],
            bpm_min=130,
            bpm_max=150
        )

        state = await use_case.start_performance(
            event=event,
            profile=profile,
            style=style_enum,
            venue=venue_enum,
            duration=duration,
            theme=theme or None
        )

        return {
            "status": "started",
            "event": state.event_name,
            "bpm": state.current_bpm,
            "style": state.current_style.value,
            "venue": state.venue_type.value,
            "tracks_buffered": len(state.buffer_tracks),
        }
    except ValueError as e:
        raise HTTPException(400, f"Invalid parameter: {e}")


@router.post("/generate")
async def generate_next():
    """Generate next track for the current performance"""
    global use_case
    if not use_case:
        raise HTTPException(503, "Performance service not initialized")

    # For now, return status — full async gen requires connected ports
    return {"status": "pipeline_ready", "ports": {
        "ai_gen": use_case.ai_gen is not None,
        "audio": use_case.audio_port is not None,
        "crowd": use_case.crowd is not None,
        "storage": use_case.storage is not None,
        "voice": use_case.voice_processor is not None,
    }}


@router.get("/status")
def get_status():
    """Get current performance system status"""
    return {
        "status": "initialized" if use_case else "uninitialized",
        "use_case": use_case is not None,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HITL QUEUE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/queue")
async def create_queue_item(req: QueueRequest):
    """Create a draft generation task awaiting human approval."""
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "status": "pending_approval",
        "stage": "queued",
        "created_at": time.time(),
        "approved_at": None,
        "approved_by": None,
        "started_at": None,
        "completed_at": None,
        "params": req.model_dump(),
        "result": None,
        "error": None,
    }
    queue = _load_queue()
    queue.append(task)
    _save_queue(queue)
    return {"status": "pending_approval", "id": task_id, "task": task}


@router.post("/approve/{task_id}")
async def approve_queue_item(task_id: str, req: ApproveRequest, background_tasks: BackgroundTasks):
    """Human approves a queued task and triggers generation."""
    queue = _load_queue()
    task = _find_task(queue, task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    if task["status"] != "pending_approval":
        raise HTTPException(409, f"Task status is '{task['status']}', cannot approve")

    task["status"] = "approved"
    task["approved_at"] = time.time()
    task["approved_by"] = req.approved_by
    _save_queue(queue)

    # Trigger generation in the background.
    background_tasks.add_task(_run_approved_generation, task_id)

    return {"status": "approved", "id": task_id, "message": "Generation started in background"}


def _set_stage(task_id: str, stage: str):
    """Update the stage field for a task in the queue file."""
    queue = _load_queue()
    task = _find_task(queue, task_id)
    if task:
        task["stage"] = stage
        _save_queue(queue)


async def _run_approved_generation(task_id: str):
    """Background worker: run orchestrator and update queue."""
    queue = _load_queue()
    task = _find_task(queue, task_id)
    if not task:
        logger.error(f"Approved task {task_id} disappeared")
        return

    task["status"] = "generating"
    task["started_at"] = time.time()
    _save_queue(queue)

    try:
        params = task["params"]
        if _orchestrator is None:
            raise RuntimeError("Orchestrator not initialized")

        # ── MOA pipeline stages ──
        _set_stage(task_id, "director")
        await asyncio.sleep(0.5)  # allow FE to poll

        _set_stage(task_id, "mixer")
        await asyncio.sleep(0.5)

        _set_stage(task_id, "lyricist")
        await asyncio.sleep(0.5)

        _set_stage(task_id, "critic")
        await asyncio.sleep(0.5)

        _set_stage(task_id, "suno")

        result = await _orchestrator.decide_and_generate(
            bpm=params["bpm"],
            energy=params["energy"],
            venue=params["venue"],
            style=params["style"],
            theme=params.get("theme", ""),
        )

        queue = _load_queue()
        task = _find_task(queue, task_id)
        task["completed_at"] = time.time()

        if "error" in result:
            task["status"] = "failed"
            task["stage"] = "failed"
            task["error"] = result["error"]
        else:
            task["status"] = "complete"
            task["stage"] = "ready"
            task["result"] = {
                "audio_url": result.get("audio_url"),
                "task_id": result.get("task_id"),
                "agent_output": result.get("agent_output"),
            }
        _save_queue(queue)

    except Exception as e:
        queue = _load_queue()
        task = _find_task(queue, task_id)
        task["status"] = "failed"
        task["stage"] = "failed"
        task["error"] = str(e)
        task["completed_at"] = time.time()
        _save_queue(queue)


@router.get("/status/{task_id}")
def get_queue_status(task_id: str):
    """Poll the state of a queued task — includes stage for MOA pipeline progress."""
    queue = _load_queue()
    task = _find_task(queue, task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return {
        "id": task_id,
        "status": task["status"],
        "stage": task.get("stage", "queued"),
        "error": task.get("error"),
        "created_at": task.get("created_at"),
    }


@router.get("/result/{task_id}")
def get_queue_result(task_id: str):
    """Get the final result of a queued task."""
    queue = _load_queue()
    task = _find_task(queue, task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    if task["status"] not in ("complete", "failed"):
        raise HTTPException(409, f"Task status is '{task['status']}', not ready")
    return {"id": task_id, "status": task["status"], "result": task.get("result"), "error": task.get("error")}


@router.get("/queue")
def list_queue():
    """List all queued tasks."""
    return {"queue": _load_queue()}


# ═══════════════════════════════════════════════════════════════════════════════
# COMMIT AUTO-FLOW (replaces HITL approve pattern)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/commit")
async def auto_commit(background_tasks: BackgroundTasks):
    """Auto-commit next generation: creates a task and fires it immediately."""
    req = QueueRequest()
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "status": "committed",
        "stage": "queued",
        "created_at": time.time(),
        "approved_at": None,
        "approved_by": "auto-commit",
        "started_at": time.time(),
        "completed_at": None,
        "params": req.model_dump(),
        "result": None,
        "error": None,
    }
    queue = _load_queue()
    queue.append(task)
    _save_queue(queue)
    background_tasks.add_task(_run_approved_generation, task_id)
    return {
        "status": "committed",
        "id": task_id,
        "message": "Generation auto-triggered (commit flow)",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CHUNKED AUDIO STREAMING
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/stream/{task_id}")
async def stream_audio(task_id: str):
    """
    Stream audio from a completed generation task using chunked transfer encoding.

    Downloads the audio URL from CometAPI's fetch result and streams it back,
    allowing the browser to start playing as chunks arrive instead of waiting
    for the full download.

    Args:
        task_id: The task ID from the queue.
    """
    queue = _load_queue()
    task = _find_task(queue, task_id)

    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")

    if task.get("status") != "complete":
        raise HTTPException(409, f"Task status is '{task['status']}', must be 'complete' to stream")

    result = task.get("result") or {}
    audio_url = result.get("audio_url")

    if not audio_url:
        raise HTTPException(404, "No audio URL found for this task")

    async def _audio_streamer():
        """Generator that yields audio chunks from the remote URL."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                async with client.stream("GET", audio_url) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        yield chunk
        except Exception as e:
            logger.error(f"Stream error for {audio_url}: {e}")
            # Yield nothing — the stream just ends
            return

    return StreamingResponse(
        _audio_streamer(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="massloop_{task_id}.mp3"',
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
        },
    )


@router.get("/buffer_health")
def buffer_health():
    """Stage buffer status — for monitor and hardware LEDs."""
    queue = _load_queue()
    ready = [t for t in queue if t["status"] == "complete"]
    generating = [t for t in queue if t["status"] == "generating"]
    pending = [t for t in queue if t["status"] in ("pending_approval", "committed")]
    buffer_tracks = len(ready)
    return {
        "buffer_tracks": buffer_tracks,
        "generating": len(generating),
        "pending": len(pending),
        "healthy": buffer_tracks >= 2,
        "status": "healthy" if buffer_tracks >= 2 else "critical" if buffer_tracks == 0 else "degraded",
        "warning": None if buffer_tracks >= 2 else "low buffer",
    }

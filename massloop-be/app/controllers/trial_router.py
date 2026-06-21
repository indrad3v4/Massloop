"""Trial router - Free 2-track mix trial gating"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time
import uuid
import json
import os
from pathlib import Path
from app.controllers.performance_router import _load_queue, _save_queue, _run_approved_generation

router = APIRouter(prefix="/api/trial", tags=["trial"])

# Production-safe: resolves relative to repo root or uses env var
_DATA_DIR = Path(__file__).parent.parent.parent / "data"
TRIAL_LIMIT_FILE = Path(os.getenv("MASSLOOP_DATA_DIR", str(_DATA_DIR))) / "trial_limits.json"


class TrialRequest(BaseModel):
    prompt: str = "Massloop trial"
    tags: str = "deep house minimal"
    bpm: int = 124
    energy: float = 0.7
    venue: str = "club"
    style: str = "deep house"


def _check_trial_quota(user_id: str = "anon") -> bool:
    """True if user still has trial available."""
    if not TRIAL_LIMIT_FILE.exists():
        return True
    try:
        data = {}
        with open(TRIAL_LIMIT_FILE) as f:
            data = json.load(f)
        return not data.get(user_id, {}).get("used", False)
    except Exception:
        return True


def _mark_trial_used(user_id: str = "anon"):
    """Mark trial as used for this user."""
    TRIAL_LIMIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if TRIAL_LIMIT_FILE.exists():
        try:
            with open(TRIAL_LIMIT_FILE) as f:
                data = json.load(f)
        except Exception:
            pass
    data[user_id] = {"used": True, "used_at": time.time()}
    with open(TRIAL_LIMIT_FILE, "w") as f:
        json.dump(data, f, indent=2)


@router.post("/start")
async def start_trial(req: TrialRequest, user_id: str = "anon"):
    """Start a free 2-track mix trial. Returns task_id."""
    if not _check_trial_quota(user_id):
        raise HTTPException(403, "Trial already used. Upgrade to DJ Starter for more.")

    # Reuse HITL queue: create task, auto-approve
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "status": "pending_approval",
        "created_at": time.time(),
        "approved_at": None,
        "approved_by": "trial_auto",
        "started_at": None,
        "completed_at": None,
        "params": req.model_dump(),
        "result": None,
        "error": None,
        "trial": True,
    }
    queue = _load_queue()
    queue.append(task)
    _save_queue(queue)

    # Auto-approve and run in background
    task["status"] = "approved"
    task["approved_at"] = time.time()
    _save_queue(queue)

    # Trigger generation
    import asyncio
    asyncio.create_task(_run_approved_generation(task_id))

    # Mark trial used
    _mark_trial_used(user_id)

    return {"status": "trial_started", "task_id": task_id}


@router.get("/result/{task_id}")
def get_trial_result(task_id: str):
    """Get result of trial generation (2-track mix)."""
    queue = _load_queue()
    for task in queue:
        if task.get("id") == task_id:
            if task["status"] not in ("complete", "failed"):
                raise HTTPException(409, f"Task status: {task['status']}")
            return {
                "id": task_id,
                "status": task["status"],
                "trial": task.get("trial", False),
                "result": task.get("result"),
                "error": task.get("error"),
            }
    raise HTTPException(404, f"Task '{task_id}' not found")
